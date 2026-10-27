"""Prefix-sensitive repair of encoded copy regions, restricted experiment."""
import argparse
import importlib.util
import random
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
q=module('pr_tools',ROOT/'research/isotope-swizzle/prototype.py')
m=module('pr_matrix',ROOT/'research/copy-centralizer/model.py')

def difference(a,b):return [x^y for x,y in zip(a,b)]
def weight(row):return bin(row).count('1')
def basis(rows):
    piv={}
    for row in sorted(set(rows),key=lambda r:(weight(r),r)):
        while row:
            k=row.bit_length()-1
            if k not in piv:piv[k]=row;break
            row^=piv[k]
    return [piv[k] for k in sorted(piv,reverse=True)]
def coordinates(rows,base):
    out=[]
    for row in rows:
        mask=0
        for j,v in enumerate(base):
            if row & (1<<(v.bit_length()-1)):row^=v;mask^=1<<j
        if row:raise ValueError('outside span')
        out.append(mask)
    assert m.product(out,base)==rows
    return out
def encoding(n,seed):
    rng=random.Random(seed);b=m.ident(n)
    for _ in range(6*n):
        i,j=rng.sample(range(n),2);b[i]^=b[j]
    assert m.inverse(b) is not None
    return b
def plan(n,ops,b):
    inv=m.inverse(b)
    if inv is None:raise ValueError('singular B')
    prefix=m.ident(n);ds=[[0]*n];eager=[]
    for op in ops:
        c=m.matrix(n,op)
        if op[2]<=0:raise ValueError('positive copy length required')
        prefix=m.product(c,prefix)
        ds.append(difference(m.product(m.product(b,prefix),inv),prefix))
        delta=difference(m.product(m.product(b,c),inv),c)
        v=basis(delta);eager.append(dict(v=v,u=coordinates(delta,v)))
    v=basis([r for d in ds for r in d]);us=[coordinates(d,v) for d in ds]
    return dict(matrix=b,inverse=inv,delta=ds,v=v,u=us,eager=eager,joint_rank=len(v),
                prefix_ranks=[len(basis(d)) for d in ds],eager_ranks=[len(e['v']) for e in eager])

def c(x):return f'(i32.const {x&0xffffffff})'
def get(i):return f'(local.get {i})'
def load(i):return f'(i32.load8_u {c(i)})'
def xor(xs):
    xs=list(xs)
    if not xs:return c(0)
    value=xs[0]
    for x in xs[1:]:value=f'(i32.xor {value} {x})'
    return value
def linear(row,reader):return xor(reader(i) for i in m.bits(row))
def snapshot(v):return ' '.join(f'(local.set {i+1} {linear(row,load)})' for i,row in enumerate(v))
def patch(u):return ' '.join(f'(i32.store8 {c(i)} (i32.xor {load(i)} {linear(row,lambda j:get(j+1))}))' for i,row in enumerate(u) if row)
def rawcopy(op,index):
    d,s,l=op
    return f'(memory.copy (select {c(65536)} {c(d)} (i32.eq {get(0)} {c(index)})) {c(s)} {c(l)})'
def blob(data):return ''.join('\\'+format(x,'02x') for x in data)

def wat(data,ops,b=None,mode='plain'):
    n=len(data);b=b if b is not None else m.ident(n);info=plan(n,ops,b)
    if mode not in ('plain','eager','full','basis','bad'):raise ValueError('mode')
    physical=bytes(data) if mode=='plain' else m.apply(b,data)
    inv=m.ident(n) if mode=='plain' else info['inverse']
    parts=[];locals_=0
    if mode=='eager':locals_=max(len(e['v']) for e in info['eager'])
    elif mode in ('basis','bad'):
        locals_=len(info['v']);parts.append(snapshot(info['v']))
    elif mode=='full':
        locals_=n;parts.append(snapshot(m.ident(n)))
    for j,op in enumerate(ops):
        if mode=='eager':parts.append(snapshot(info['eager'][j]['v']))
        if mode in ('basis','full') and j:
            fix=patch(info['u'][j] if mode=='basis' else info['delta'][j])
            parts.append(f'(if (i32.eq {get(0)} {c(j)}) (then {fix}))')
        parts.append(rawcopy(op,j))
        if mode=='eager':parts.append(patch(info['eager'][j]['u']))
    if mode in ('basis','bad','full'):parts.append(patch(info['delta'][-1] if mode=='full' else info['u'][-1]))
    declarations='(local '+' '.join(['i32']*locals_)+')' if locals_ else ''
    run='(func (export "run") (param i32) '+declarations+' '+' '.join(parts)+')'
    digest=['(local.set 0 '+c(2166136261)+')']
    for row in inv:
        digest.append(f'(local.set 0 (i32.mul (i32.xor {get(0)} {linear(row,load)}) {c(16777619)}))')
    observe='(func (export "digest") (result i32) (local i32) '+' '.join(digest)+' '+get(0)+')'
    return '(module (memory 1 1) '+run+observe+' (data '+c(0)+' "'+blob(physical)+'"))'

def data_image(mod):
    ds=[e for e in mod[1:] if e[0]=='data']
    if len(ds)!=1 or ds[0][1]!=['i32.const','0']:raise ValueError('single data segment')
    out=[]
    for s in ds[0][2:]:
        i=1
        while i<len(s)-1:
            if s[i]=='\\':
                if s[i+1] in '0123456789abcdefABCDEF' and s[i+2] in '0123456789abcdefABCDEF':out.append(int(s[i+1:i+3],16));i+=3
                else:out.append({'n':10,'t':9,'r':13,'"':34,"'":39,'\\':92}[s[i+1]]);i+=2
            else:out.append(ord(s[i]));i+=1
    return bytes(out)

def parse(src):
    mod=q.read(src);data=data_image(mod);fs=[e for e in mod[1:] if e[0]=='func']
    if len(fs)!=2 or not 2<=len(data)<=64:raise ValueError('closed two-function 2..64-byte profile')
    body=[e for e in fs[0][1:] if e[0] not in ('type','param','result','local')];ops=[]
    for j,e in enumerate(body):
        if e[0]!='memory.copy' or len(e)!=4 or e[1][0]!='select':raise ValueError('guarded native copy sequence')
        d=int(e[1][2][1],0);s=int(e[2][1],0);l=int(e[3][1],0);ops.append((d,s,l))
    if not 1<=len(ops)<=16:raise ValueError('1..16 copy operations')
    for op in ops:m.copy_map(len(data),op)
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='prefix-repair-') as td:
        ref=Path(td)/'source.wasm';q.compile(wat(data,ops),ref)
        if q.read(ref)!=mod:raise ValueError('source differs from the closed profile')
    return data,ops

def transform(src,dst,mode,seed=211070):
    t=time.perf_counter();data,ops=parse(src);b=encoding(len(data),seed);info=plan(len(data),ops,b)
    q.compile(wat(data,ops,b,mode),dst)
    return dict(mode=mode,seed=seed,n=len(data),ops=ops,**info,transform_ms=(time.perf_counter()-t)*1000)

def probe(src,dst):
    mod=q.read(src);mod.append(['export','"memory"',['memory','0']]);q.compile(q.w.emit(mod),dst)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['eager','full','basis'],default='basis');ap.add_argument('--seed',type=int,default=211070)
    a=ap.parse_args();q.save(str(a.output)+'.json',transform(a.source,a.output,a.mode,a.seed))
