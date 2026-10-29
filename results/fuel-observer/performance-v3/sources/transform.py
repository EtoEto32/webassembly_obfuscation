"""Finite public-history cost envelope, using structural paths as an overapproximation."""
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
START=-2147483648
BINARY={'i32.'+op for op in ('add','sub','mul','and','or','xor','shl','shr_u','eq','ne','lt_u','le_u','gt_u','ge_u')}


def expression(x,n,depth=0):
    if depth>48 or not isinstance(x,list) or not x:raise ValueError('expression depth or shape')
    if x[0]=='i32.const' and len(x)==2:int(x[1]);return 1
    if x[0]=='local.get' and len(x)==2 and 0<=int(x[1])<n:return 1
    if x[0]=='i32.eqz' and len(x)==2:return 1+expression(x[1],n,depth+1)
    if x[0] in BINARY and len(x)==3:return 1+expression(x[1],n,depth+1)+expression(x[2],n,depth+1)
    raise ValueError('unsupported expression '+w.emit(x))


def coalesce(paths):
    """Pointwise maxima for equal public words, at a common continuation."""
    groups={}
    for p in paths:
        key=tuple(tuple(e['label']) for e in p['events'])
        if key not in groups:groups[key]=copy.deepcopy(p);continue
        q=groups[key];q['total']=max(q['total'],p['total']);q['multiplicity']+=p['multiplicity']
        for a,b in zip(q['events'],p['events']):a['cost']=max(a['cost'],b['cost'])
    return list(groups.values())


def sequence(body,n,paths=None,depth=0,merge_histories=False):
    if depth>32:raise ValueError('statement depth')
    paths=paths or [{'events':[],'total':0,'multiplicity':1}]
    for x in body:
        if not isinstance(x,list) or not x:raise ValueError('statement shape')
        op=x[0]
        if op=='if':
            if len(x) not in (3,4) or x[2][0]!='then' or (len(x)==4 and x[3][0]!='else'):raise ValueError('void if only')
            c=1+expression(x[1],n);nextpaths=[]
            for p in paths:
                q=copy.deepcopy(p);q['total']+=c
                for arm in (x[2][1:],x[3][1:] if len(x)==4 else []):nextpaths.extend(sequence(arm,n,[copy.deepcopy(q)],depth+1,merge_histories))
            paths=nextpaths
        elif op=='call':
            if len(x)!=4 or x[1]!='0' or any(y[0]!='i32.const' or len(y)!=2 for y in x[2:]):raise ValueError('constant two-argument marker only')
            label=[int(x[2][1]),int(x[3][1])]
            if not 0<=label[0]<2**31 or not -(2**31)<=label[1]<2**31:raise ValueError('marker label')
            for p in paths:p['total']+=3;p['events'].append({'label':label,'cost':p['total']})
        else:
            if op=='local.set' and len(x)==3 and 0<=int(x[1])<n:c=1+expression(x[2],n)
            elif op=='drop' and len(x)==2:c=1+expression(x[1],n)
            elif op=='nop' and len(x)==1:c=1
            else:c=expression(x,n)
            for p in paths:p['total']+=c
        if merge_histories:paths=coalesce(paths)
        if len(paths)>4096 or any(len(p['events'])>32 for p in paths):raise ValueError('path/event budget exceeded')
    return paths


def envelope(paths):
    nodes=[];depth_bounds={};terminal_bounds={}
    def build(history,selected):
        i=len(history);index=len(nodes)
        before=max((p['events'][i-1]['cost'] if i else 0) for p in selected)
        bound=max(p['events'][i]['cost'] if len(p['events'])>i else p['total'] for p in selected)
        assert bound>=before
        terminal=[p['total'] for p in selected if len(p['events'])==i]
        node={'history':history,'bound':bound,'pastBound':before,'terminalBound':max(terminal) if terminal else None,'next':{}}
        nodes.append(node);depth_bounds[i]=max(depth_bounds.get(i,0),bound)
        if terminal:terminal_bounds[i]=max(terminal_bounds.get(i,0),max(terminal))
        labels=sorted(set(tuple(p['events'][i]['label']) for p in selected if len(p['events'])>i))
        for label in labels:
            chosen=[p for p in selected if len(p['events'])>i and tuple(p['events'][i]['label'])==label]
            node['next'][','.join(map(str,label))]=build(history+[list(label)],chosen)
        return index
    build([],paths)
    return {'nodes':nodes,'depthBounds':[depth_bounds[i] for i in range(max(depth_bounds)+1)],'terminalBounds':terminal_bounds,'whole':max(p['total'] for p in paths)}


def analyze(src,merge_histories=False):
    if src.stat().st_size>131072:raise ValueError('binary limit')
    w.tool('wasm-validate',[src]);m=w.parse(w.tool('wasm2wat',[src,'--fold-exprs','--no-debug-names']))
    if any(x[0] not in ('type','import','func','export') for x in m[1:]):raise ValueError('module subset')
    im=[x for x in m[1:] if x[0]=='import'];fs=[x for x in m[1:] if x[0]=='func'];ex=[x for x in m[1:] if x[0]=='export']
    if len(im)!=1 or im[0][1:3]!=['"env"','"mark"'] or im[0][3][0]!='func' or len(fs)!=1 or ex!=[['export','"run"',['func','1']]]:raise ValueError('single marker import and run export required')
    types=[x for x in m[1:] if x[0]=='type'];ti=int(im[0][3][1][1])
    if types[ti][1]!=['func',['param','i32','i32']]:raise ValueError('marker type')
    f=fs[0];decl=[x for x in f[1:] if x[0] in ('type','param','result','local')]
    if [x for x in decl if x[0]=='param']!=[['param','i32','i32']] or [x for x in decl if x[0]=='result']!=[['result','i32']]:raise ValueError('run signature')
    localdecl=[x for x in decl if x[0]=='local']
    if any(v!='i32' for x in localdecl for v in x[1:]):raise ValueError('local type')
    n=2+sum(len(x)-1 for x in localdecl)
    if n>64:raise ValueError('local limit')
    body=[x for x in f[1:] if x not in decl];paths=sequence(body,n,merge_histories=merge_histories)
    return m,f,decl,body,paths,envelope(paths)


def transform(src,dest,merge_histories=False):
    begin=time.perf_counter();m,f,decl,body,paths,env=analyze(src,merge_histories)
    f[:]=['func',*decl,['call','0',['i32.const',str(START)],['i32.const','0']],*body]
    dest.parent.mkdir(parents=True,exist_ok=True);wat=dest.with_suffix('.wat');wat.write_text(w.emit(m),encoding='utf8')
    w.tool('wat2wasm',[wat,'-o',dest]);w.tool('wasm-validate',[dest])
    report={'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'targetSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'sourceBytes':src.stat().st_size,'targetBytes':dest.stat().st_size,'seconds':time.perf_counter()-begin,'pathCount':sum(p['multiplicity'] for p in paths),'rowCount':len(paths),'mergeHistories':merge_histories,'paths':paths,**env}
    dest.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf8');return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('target',type=Path);p.add_argument('--merge-histories',action='store_true');a=p.parse_args();r=transform(a.source,a.target,a.merge_histories);print(json.dumps({k:r[k] for k in ('pathCount','rowCount','sourceBytes','targetBytes','seconds')}))
