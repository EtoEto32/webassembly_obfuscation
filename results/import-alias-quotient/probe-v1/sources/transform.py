"""Memory-import quotient for differential validation, not an isolation boundary."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('wat_helper',ROOT/'research/connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
MEMARG={'i32.load','i32.load8_s','i32.load8_u','i32.load16_s','i32.load16_u','i32.store','i32.store8','i32.store16'}
SIMPLE={'func','type','param','result','local','block','if','then','else','return','call','br','br_if','drop','nop','unreachable','select','local.get','local.set','local.tee','data.drop'}
SIMPLE|={'i32.'+x for x in ('const','add','sub','mul','and','or','xor','shl','shr_u','shr_s','rotl','rotr','eq','ne','eqz','lt_u','lt_s','gt_u','gt_s','le_u','le_s','ge_u','ge_s','clz','ctz','popcnt')}


def quotient(src,dest,partition):
    begin=time.perf_counter()
    if src.stat().st_size>131072:raise ValueError('binary too large')
    w.tool('wasm-validate',[src]);m=w.parse(w.tool('wasm2wat',[src,'--fold-exprs']))
    if any(x[0] not in ('type','import','func','export','data','start') for x in m[1:]):raise ValueError('module section outside subset')
    imports=[x for x in m[1:] if x[0]=='import']
    if not 1<=len(imports)<=4 or any(x[3][0]!='memory' for x in imports):raise ValueError('only 1..4 memory imports')
    if any(x[3][1:]!=['1','3'] for x in imports):raise ValueError('initial subset: memory32 unshared limits 1 3')
    if len(set((x[1],x[2]) for x in imports))!=len(imports):raise ValueError('distinct import names required')
    if len(partition)!=len(imports):raise ValueError('partition arity')
    seen=[]
    for v in partition:
        if not isinstance(v,int) or isinstance(v,bool) or v<0 or v>len(seen):raise ValueError('restricted growth partition required')
        if v==len(seen):seen.append(v)
    def mem(v):
        i=int(v)
        if not 0<=i<len(partition):raise ValueError('memory index')
        return str(partition[i])
    counts={'nodes':0,'memorySites':0}
    def rewrite(x,depth=0):
        counts['nodes']+=1
        if depth>64 or counts['nodes']>20000:raise ValueError('AST limit')
        if not isinstance(x,list) or not x:raise ValueError('AST shape')
        op=x[0];y=copy.deepcopy(x)
        if op in MEMARG or op in ('memory.size','memory.grow','memory.fill'):
            i=1
            if len(x)>1 and isinstance(x[1],str) and x[1].isdigit():i=2;index=x[1]
            else:index='0'
            y=[op,mem(index),*copy.deepcopy(x[i:])];counts['memorySites']+=1
        elif op=='memory.copy':
            prefix=[v for v in x[1:] if isinstance(v,str)]
            if len(prefix) not in (0,2):raise ValueError('memory.copy immediate shape')
            indices=prefix or ['0','0'];y=[op,*map(mem,indices),*copy.deepcopy(x[1+len(prefix):])];counts['memorySites']+=1
        elif op=='memory.init':
            prefix=[v for v in x[1:] if isinstance(v,str)]
            if len(prefix) not in (1,2):raise ValueError('memory.init immediate shape')
            index,data=(prefix if len(prefix)==2 else ['0',prefix[0]])
            y=[op,mem(index),data,*copy.deepcopy(x[1+len(prefix):])];counts['memorySites']+=1
        elif op not in SIMPLE:raise ValueError('unsupported AST node '+op)
        if op in ('param','result','local') and any(v!='i32' for v in y[1:]):raise ValueError('i32 subset')
        for i in range(1,len(y)):
            if isinstance(y[i],list):y[i]=rewrite(y[i],depth+1)
        return y
    result=['module'];import_i=0;kept=set()
    for x in m[1:]:
        if x[0]=='import':
            p=partition[import_i];import_i+=1
            if p not in kept:result.append(copy.deepcopy(x));kept.add(p)
        elif x[0]=='export':
            y=copy.deepcopy(x)
            if y[2][0]=='memory':y[2][1]=mem(y[2][1])
            elif y[2][0]!='func':raise ValueError('unsupported export')
            result.append(y)
        elif x[0]=='data':
            y=copy.deepcopy(x)
            if isinstance(y[1],list):
                if y[1][0]=='memory':y[1][1]=mem(y[1][1])
                else:y.insert(1,['memory',mem('0')])
                if y[2][0]!='i32.const':raise ValueError('constant data offset required')
            result.append(y)
        elif x[0]=='start':result.append(copy.deepcopy(x))
        else:result.append(rewrite(x))
    dest.parent.mkdir(parents=True,exist_ok=True);dest.with_suffix('.wat').write_text(w.emit(result),encoding='utf8')
    w.tool('wat2wasm',[dest.with_suffix('.wat'),'-o',dest]);w.tool('wasm-validate',[dest])
    report={'partition':partition,'inputImports':[[x[1][1:-1],x[2][1:-1]] for x in imports],
      'representatives':[partition.index(v) for v in seen],'memorySites':counts['memorySites'],
      'inputSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'outputSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),
      'inputBytes':src.stat().st_size,'outputBytes':dest.stat().st_size,'seconds':time.perf_counter()-begin}
    dest.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf8');return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--partition',required=True)
    a=ap.parse_args();print(json.dumps(quotient(a.input,a.output,[int(v) for v in a.partition.split(',')]),indent=2))
