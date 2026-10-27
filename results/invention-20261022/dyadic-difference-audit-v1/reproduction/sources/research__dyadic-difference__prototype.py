"""Restricted i32 polynomial -> dyadic finite-difference evaluator."""
import argparse, importlib.util, math, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('difference_tools',ROOT/'research/isotope-swizzle/prototype.py')
q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
MASK=2**32-1


def trim(a):
    a=[x&MASK for x in a]
    while len(a)>1 and not a[-1]:a.pop()
    return a


def add(a,b,sign=1):
    out=[0]*max(len(a),len(b))
    for i,x in enumerate(a):out[i]+=x
    for i,x in enumerate(b):out[i]+=sign*x
    return trim(out)


def mul(a,b):
    if len(a)+len(b)>34:raise ValueError('polynomial degree cap')
    out=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return trim(out)


def evaluate(a,x):
    v=0
    for c in reversed(a):v=(v*x+c)&MASK
    return v


def difference(a,h):
    out=[0]*len(a)
    for n,c in enumerate(a):
        for k in range(n):out[k]+=c*math.comb(n,k)*pow(h,n-k)
    return trim(out)


def c(x):return f'(i32.const {x&MASK})'


def horner(a,x='(local.get 0)'):
    a=trim(a);result=c(a[-1])
    for v in reversed(a[:-1]):result=f'(i32.add (i32.mul {result} {x}) {c(v)})'
    return result


def source(a):return '(module (func (export "run") (param i32) (result i32) '+horner(a)+'))'


def polynomial(f):
    if [v for e in f[1:] if e[0]=='param' for v in e[1:]]!=['i32']:raise ValueError('one i32 parameter')
    if [v for e in f[1:] if e[0]=='result' for v in e[1:]]!=['i32']:raise ValueError('one i32 result')
    env=[[0,1]]
    for e in f[1:]:
        if e[0]=='local':
            if any(x!='i32' for x in e[1:]):raise ValueError('integer locals only')
            env += [[0]]*len(e[1:])
    def walk(e):
        op=e[0]
        if op=='local.get':return env[int(e[1])]
        if op=='i32.const':return [int(e[1],0)&MASK]
        if op in ('local.set','local.tee'):
            v=walk(e[2]);env[int(e[1])]=v;return v if op=='local.tee' else None
        if op in ('i32.add','i32.sub'):return add(walk(e[1]),walk(e[2]),1 if op=='i32.add' else -1)
        if op=='i32.mul':return mul(walk(e[1]),walk(e[2]))
        if op=='i32.shl' and e[2][0]=='i32.const':return mul(walk(e[1]),[1<<(int(e[2][1],0)&31)])
        raise ValueError('non-polynomial instruction '+op)
    value=None
    for e in f[1:]:
        if e[0] not in ('type','param','result','local'):value=walk(e)
    if value is None:raise ValueError('missing return value')
    return value


def parse(src):
    m=q.read(src)
    if any(e[0] not in ('type','func','export') for e in m[1:]):raise ValueError('pure module required')
    fs=[e for e in m[1:] if e[0]=='func']
    if len(fs)!=1:raise ValueError('one source function')
    a=polynomial(fs[0])
    if not 2<=len(a)-1<=12:raise ValueError('degree 2..12')
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='difference-source-') as td:
        f=Path(td)/'canonical.wasm';q.compile(source(a),f)
        if q.read(f)!=m:raise ValueError('canonical source profile')
    return a


def driver(initial):
    return f'''(func (export "run") (param i32) (result i32) (local i32 i32 i32 i32)
      (local.set 2 {c(initial)})
      (block (loop
        (br_if 1 (i32.ge_u (local.get 3) (i32.const 32)))
        (local.set 4 (i32.shl (i32.const 1) (local.get 3)))
        (if (i32.and (local.get 0) (local.get 4)) (then
          (local.set 2 (i32.add (local.get 2) (call_indirect (type 0) (local.get 1) (local.get 3))))
          (local.set 1 (i32.add (local.get 1) (local.get 4)))))
        (local.set 3 (i32.add (local.get 3) (i32.const 1))) (br 0)))
      (local.get 2))'''


def assemble(helpers,initial):
    return '(module (type (func (param i32) (result i32))) (table 32 32 funcref) '+' '.join(helpers)+' '+driver(initial)+' (elem (i32.const 0) func '+' '.join(map(str,range(32)))+'))'


def transformed(a,mode):
    hs=[]
    for i in range(32):
        h=1<<i
        if mode=='delta':e=horner(difference(a,h))
        elif mode=='naive':e=f'(i32.sub {horner(a,f"(i32.add (local.get 0) {c(h)})")} {horner(a)})'
        elif mode=='bad':e=horner([h*j*a[j] for j in range(1,len(a))])
        else:raise ValueError('mode')
        hs.append('(func (param i32) (result i32) '+e+')')
    return assemble(hs,a[0])


def transform(src,dst,mode='delta'):
    start=time.perf_counter();a=parse(src);q.compile(transformed(a,mode),dst)
    return dict(degree=len(a)-1,mode=mode,transform_ms=(time.perf_counter()-start)*1000)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['delta','naive'],default='delta');a=ap.parse_args()
    q.save(str(a.output)+'.json',transform(a.source,a.output,a.mode))
