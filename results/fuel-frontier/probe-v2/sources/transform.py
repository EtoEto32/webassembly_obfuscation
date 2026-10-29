"""Restricted Core Wasm: public-event prefix envelopes and prepaid accounting.

Logical original-opcode costs, NOT V8/Wasmtime engine fuel or a CPU-time bound.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('wat_helper', ROOT/'research/connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
BIN = {'i32.'+x for x in ('add','sub','mul','and','or','xor','shl','shr_u','shr_s','rotl','rotr','eq','ne','lt_u','lt_s','le_u','le_s','gt_u','gt_s','ge_u','ge_s')}
UN = {'i32.'+x for x in ('eqz','clz','ctz','popcnt')}
MODES = ('dynamic','late','whole','segment','frontier')


def expr_cost(x, locals_count, depth=0):
    if depth > 64 or not isinstance(x, list) or not x:
        raise ValueError('expression nesting/shape')
    op=x[0]
    if op=='i32.const' and len(x)==2:
        int(x[1]); return 1
    if op=='local.get' and len(x)==2 and 0<=int(x[1])<locals_count:
        return 1
    if op in UN and len(x)==2:
        return 1+expr_cost(x[1],locals_count,depth+1)
    if op in BIN and len(x)==3:
        return 1+sum(expr_cost(v,locals_count,depth+1) for v in x[1:])
    raise ValueError('unsupported expression: '+w.emit(x))


def empty(): return {'events':[], 'prefix':[0], 'segment':[0]}


def concat(a,b):
    # Abstract paths in sequential constructs may choose conditions independently.
    # This is conservative when predicates correlate across separate constructs.
    return {'events':a['events']+b['events'],
            'prefix':a['prefix'][:-1]+[a['prefix'][-1]+v for v in b['prefix']],
            'segment':a['segment'][:-1]+[a['segment'][-1]+b['segment'][0]]+b['segment'][1:]}


def analyze_seq(body,n,depth=0):
    if depth>64: raise ValueError('statement nesting')
    out=empty()
    for x in body:
        if not isinstance(x,list) or not x: raise ValueError('statement shape')
        op=x[0]
        if op in ('local.set','drop'):
            if op=='local.set':
                if len(x)!=3 or not 0<=int(x[1])<n: raise ValueError('local.set')
            elif len(x)!=2: raise ValueError('drop')
            c=1+expr_cost(x[-1],n); s={'events':[], 'prefix':[c], 'segment':[c]}
        elif op=='call':
            if len(x)!=3 or x[1]!='0' or x[2][0]!='i32.const':
                raise ValueError('only constant public marker import is supported')
            c=1+expr_cost(x[2],n)
            s={'events':[int(x[2][1]) & 0xffffffff], 'prefix':[c,c], 'segment':[c,0]}
        elif op=='if':
            if len(x)!=4 or x[2][0]!='then' or x[3][0]!='else':
                raise ValueError('only void if with explicit else')
            c=1+expr_cost(x[1],n)
            a=analyze_seq(x[2][1:],n,depth+1); b=analyze_seq(x[3][1:],n,depth+1)
            if a['events']!=b['events']: raise ValueError('branch public event words differ')
            s={'events':a['events'], 'prefix':[c+max(u,v) for u,v in zip(a['prefix'],b['prefix'])],
               'segment':[max(u,v) for u,v in zip(a['segment'],b['segment'])]}
            s['segment'][0]+=c
        else:
            # Only the final result expression is allowed by the Wasm validator.
            c=expr_cost(x,n); s={'events':[], 'prefix':[c], 'segment':[c]}
        out=concat(out,s)
        if len(out['events'])>256 or max(out['prefix'])>2**53-1:
            raise ValueError('analysis bound')
    return out


def read_module(src):
    if src.stat().st_size>131072: raise ValueError('binary size bound')
    w.tool('wasm-validate',[src])
    m=w.parse(w.tool('wasm2wat',[src,'--fold-exprs']))
    if any(x[0] not in ('type','import','func','export') for x in m[1:]):
        raise ValueError('unsupported module section')
    imp=[x for x in m[1:] if x[0]=='import']; funcs=[x for x in m[1:] if x[0]=='func']
    exports=[x for x in m[1:] if x[0]=='export']
    if len(imp)!=1 or imp[0][1:3]!=['"env"','"mark"'] or len(funcs)!=1:
        raise ValueError('expected one marker import and one definition')
    types=[x for x in m[1:] if x[0]=='type']
    ti=int(imp[0][3][1][1])
    if imp[0][3][0]!='func' or types[ti][1]!=['func',['param','i32']]:
        raise ValueError('marker signature')
    if exports!=[['export','"run"',['func','1']]]: raise ValueError('expected run export')
    f=funcs[0]
    decl=[x for x in f[1:] if x[0] in ('type','param','result','local')]
    if [x for x in decl if x[0]=='result']!=[['result','i32']]: raise ValueError('i32 result required')
    params=[t for x in decl if x[0]=='param' for t in x[1:]]
    locals_=[t for x in decl if x[0]=='local' for t in x[1:]]
    if any(t!='i32' for t in params+locals_) or len(params+locals_)>128:
        raise ValueError('i32 local subset')
    body=[x for x in f[1:] if x[0] not in ('type','param','result','local')]
    if not body: raise ValueError('empty body')
    expr_cost(body[-1],len(params+locals_))
    summary=analyze_seq(body,len(params+locals_))
    return m, f, decl, body, len(params), len(params+locals_), summary


def charge(v): return ['call','1',['i64.const',str(v)]]


def transform(src, dest, mode):
    if mode not in MODES: raise ValueError('mode')
    start=time.perf_counter()
    m,f,decl,body,params,n,s=read_module(src)
    s['delta']=[s['prefix'][0]]+[b-a for a,b in zip(s['prefix'],s['prefix'][1:])]
    if any(v<0 for v in s['delta']): raise AssertionError('nonmonotone envelope')
    dynamic=mode in ('dynamic','late')
    schedule=s['delta'] if mode=='frontier' else s['segment']
    def ex(x):
        y=copy.deepcopy(x)
        for i in range(1,len(y)):
            if isinstance(y[i],list): y[i]=ex(y[i])
        return ['block',['result','i32'],charge(1),y] if dynamic else y
    def seq(xs,j):
        out=[]
        for x in xs:
            op=x[0]
            if op=='if':
                if dynamic: out.append(charge(1))
                a,ja=seq(x[2][1:],j); b,jb=seq(x[3][1:],j)
                assert ja==jb
                out.append(['if',ex(x[1]),['then',*a],['else',*b]]);j=ja
            elif op=='call':
                if dynamic: out.append(charge(1))
                out.append(['call','0',ex(x[2])]); j+=1
                if mode in ('segment','frontier'): out.append(charge(schedule[j]))
            elif op in ('local.set','drop'):
                if dynamic: out.append(charge(1))
                out.append([*x[:-1],ex(x[-1])])
            else: out.append(ex(x))
        return out,j
    b,j=seq(body,0); assert j==len(s['events'])
    if mode=='whole': b.insert(0,charge(s['prefix'][-1]))
    if mode in ('segment','frontier'): b.insert(0,charge(schedule[0]))
    if mode=='late':
        decl=copy.deepcopy(decl)+[['local','i32']]
        # Preserve result while executing padding; helper bookkeeping is uncharged.
        b[-1]=['local.set',str(n),b[-1]]
        b.extend([['call','2',['i64.const',str(s['prefix'][-1])]],['local.get',str(n)]])
    new=['module']+[copy.deepcopy(x) for x in m[1:] if x[0] in ('type','import')]
    new.append(['import','"fuel"','"charge"',['func',['param','i64']]])
    if mode=='late': new.append(['import','"fuel"','"pad"',['func',['param','i64']]])
    new.extend([['func',*decl,*b],['export','"run"',['func','3' if mode=='late' else '2']]])
    dest.parent.mkdir(parents=True,exist_ok=True)
    wat=dest.with_suffix('.wat'); wat.write_text(w.emit(new),encoding='utf8')
    w.tool('wat2wasm',[wat,'-o',dest]);w.tool('wasm-validate',[dest])
    report={'mode':mode,'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
            'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'params':params,
            'summary':s,'bytes_before':src.stat().st_size,'bytes_after':dest.stat().st_size,
            'transform_seconds':time.perf_counter()-start}
    dest.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--mode',choices=MODES,default='frontier');a=ap.parse_args()
    print(json.dumps(transform(a.input,a.output,a.mode),indent=2))
