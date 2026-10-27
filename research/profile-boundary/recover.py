"""A proved expression hole in a checked profile; not arbitrary Wasm analysis."""
import argparse
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('boundary', HERE/'run.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=b.p
sys.path.insert(0,str(b.ROOT/'.tools/encoding-synthesis-python'))
import z3 as z
HOLE='__PROVED_PARTNER_EXPRESSION__'


def guard_order(m,n):
    m=copy.deepcopy(m)
    fs=[e for e in m[1:] if e[0]=='func']
    if len(fs)!=2: raise ValueError('unsupported function structure')
    f=fs[1];indices=[i for i,x in enumerate(f) if isinstance(x,list) and x[0] not in ('type','param','result','local')]
    expect=[['if',['i32.ge_u',['local.get',str(i)],['i32.const',str(n)]],['then',['unreachable']]] for i in range(3)]
    if len(indices)<3 or sorted((f[i] for i in indices[:3]),key=repr)!=sorted(expect,key=repr):
        raise ValueError('unsupported pre-update guards')
    for i,expr in zip(indices[:3],expect): f[i]=expr
    return m


def range_proof(expr,n):
    params=[z.BitVec('param%d'%i,32) for i in range(4)]
    def ev(e):
        if not isinstance(e,list) or not e: raise ValueError('unsupported expression')
        op=e[0]
        if op=='local.get' and len(e)==2 and e[1] in ('0','1','3'): return params[int(e[1])]
        if op=='i32.const' and len(e)==2: return z.BitVecVal(int(e[1],0),32)
        if op=='select' and len(e)==4:
            x,y,c=(ev(t) for t in e[1:]);return z.If(c!=0,x,y)
        if len(e)!=3 or op not in ('i32.add','i32.sub','i32.mul','i32.and','i32.or','i32.xor','i32.shl','i32.shr_u'):
            raise ValueError('unsupported or effectful partner expression')
        x,y=ev(e[1]),ev(e[2])
        if op=='i32.add':return x+y
        if op=='i32.sub':return x-y
        if op=='i32.mul':return x*y
        if op=='i32.and':return x&y
        if op=='i32.or':return x|y
        if op=='i32.xor':return x^y
        if op=='i32.shl':return x<<(y&31)
        return z.LShR(x,y&31)
    w=ev(expr);solver=z.Solver();solver.set(timeout=10000)
    solver.add(z.ULT(params[0],n),z.ULT(params[1],n),z.ULT(params[2],n),z.UGE(w,n))
    result=str(solver.check())
    if result!='unsat': raise ValueError('range proof '+result)
    return result


def capture(pattern,actual):
    found=[]
    def rec(a,c):
        if a==HOLE: found.append(c);return True
        if isinstance(a,list):return isinstance(c,list) and len(a)==len(c) and all(rec(x,y) for x,y in zip(a,c))
        return a==c
    if not rec(pattern,actual) or len(found)!=1:raise ValueError('unsupported update/observer structure')
    return found[0]


def replace_once(tree,expected):
    count=0
    def rec(e):
        nonlocal count
        if e==expected:count+=1;return HOLE
        return [rec(x) for x in e] if isinstance(e,list) else e
    result=rec(tree)
    if count!=1:raise AssertionError('template expression is not unique')
    return result


def recover(src,dst):
    start=time.perf_counter();m=p.q.read(src);values=p.data_of(m)
    if len(values)%3:raise ValueError('unsupported data')
    n=len(values)//3
    if n not in (4,8,16,32,64,128,256):raise ValueError('unsupported size')
    A,B,payload=values[:n],values[n:2*n],values[2*n:]
    if sorted(A)!=list(range(n)) or any(v>=n for v in B):raise ValueError('initial invariant fails')
    edges=[B[i] for i in A];m=guard_order(m,n)
    canonical=['i32.and',['i32.add',['i32.add',['local.get','0'],['local.get','1']],['local.get','3']],['i32.const',str(n-1)]]
    with tempfile.TemporaryDirectory(dir=b.ROOT/'tmp') as td:
        td=Path(td);raw=td/'template.wasm';p.q.compile(p.render(edges,payload,'moving',A),raw)
        target=td/'target.wasm';p.q.compile(p.q.w.emit(m),target)
        target_opt=td/'target-opt.wasm';p.q.w.tool('wasm-opt',[target,'--enable-bulk-memory','-O3','-o',target_opt])
        template_opt=td/'template-opt.wasm';p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',template_opt])
        template=replace_once(p.q.read(template_opt),canonical)
        expr=capture(template,p.q.read(target_opt))
        proof_start=time.perf_counter();status=range_proof(expr,n);proof_ms=(time.perf_counter()-proof_start)*1000
        p.q.compile(p.render(edges,payload),dst)
    return dict(n=n,range_proof=status,range_ms=proof_ms,wall_ms=(time.perf_counter()-start)*1000,expression=expr)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('output');args=a.parse_args()
    import json
    print(json.dumps(recover(args.source,args.output)))
