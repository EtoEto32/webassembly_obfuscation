# -*- coding: utf-8 -*-
"""Restricted Boolean-word Wasm -> finite-flush polynomial dynamics.

Polynomials are ANF over bitwise words. Atom 32*i+r denotes rotl(word_i,r).
No secret coordinate map or original DAG is emitted in the binary.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import struct
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('hfl_wasm',HERE.parent/'connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)
MASK=0xffffffff
MAGIC=0x314c4648
LIMIT=50000


def const(v):
    if v not in (0,MASK):raise ValueError('Only uniform 0/-1 constants')
    return {()} if v else set()


def var(i,r=0):return {(32*i+(r%32),)}
def add(a,b):return a.symmetric_difference(b)


def mul(a,b):
    out=set()
    for x in a:
        for y in b:
            m=tuple(sorted(set(x+y)))
            if m in out:out.remove(m)
            else:out.add(m)
        if len(out)>LIMIT:raise OverflowError('ANF term cap')
    return out


def rotate(a,r):
    out=set()
    for m in a:
        t=tuple(sorted((v//32)*32+(v%32+r)%32 for v in m))
        if t in out:out.remove(t)
        else:out.add(t)
    return out


def sub(a,env):
    out=set();cache={}
    for m in a:
        term={()}
        for v in m:
            if v not in cache:cache[v]=rotate(env[v//32],v%32)
            term=mul(term,cache[v])
        out=add(out,term)
        if len(out)>LIMIT:raise OverflowError('Substitution term cap')
    return out


def rank(rows):
    piv={}
    for x in rows:
        while x:
            k=x.bit_length()-1
            if k in piv:x^=piv[k]
            else:piv[k]=x;break
    return len(piv)


def inverse(rows):
    n=len(rows);a=[r|(1<<(n+i)) for i,r in enumerate(rows)]
    for j in range(n):
        k=next(i for i in range(j,n) if (a[i]>>j)&1);a[k],a[j]=a[j],a[k]
        for i in range(n):
            if i!=j and ((a[i]>>j)&1):a[i]^=a[j]
    return [r>>n for r in a]


def mix(rows,values):
    ans=[]
    for row in rows:
        z=set()
        for j,p in enumerate(values):
            if row>>j&1:z=add(z,p)
        ans.append(z)
    return ans


def source(path):
    w.tool('wasm-validate',[path]);m=w.parse(w.tool('wasm2wat',[path,'--fold-exprs']))
    if any(a[0] not in ('type','func','export') for a in m[1:]):raise ValueError('Pure function only')
    fs=[a for a in m[1:] if a[0]=='func'];ex=[a for a in m[1:] if a[0]=='export']
    if len(fs)!=1 or ex!=[['export','"run"',['func','0']]]:raise ValueError('Single run export required')
    f=fs[0];n=sum(len(a)-1 for a in f[1:] if a[0]=='param');nl=sum(len(a)-1 for a in f[1:] if a[0]=='local')
    if not 1<=n<=32 or any(t!='i32' for a in f[1:] if a[0] in ('param','local') for t in a[1:]):raise ValueError('i32 arguments only')
    if [a for a in f[1:] if a[0]=='result']!=[['result','i32']]:raise ValueError('One result')
    nodes=[];depth=[];env=[('p',i) for i in range(n)]+[('c',0)]*nl;stack=[]
    def node(op,*args):
        if len(nodes)>=24:raise ValueError('Maximum 24 DAG nodes')
        nodes.append((op,*args));depth.append(1+max([depth[v[1]] for v in args if isinstance(v,tuple) and v[0]=='s']+[0]));return ('s',len(nodes)-1)
    def execute(t):
        op=t[0]
        if op=='i32.const':stack.append(('c',int(t[1])&MASK));return
        if op=='local.get':stack.append(env[int(t[1])]);return
        for a in t[1:]:
            if isinstance(a,list):execute(a)
        if op in ('local.set','local.tee'):
            env[int(t[1])]=stack.pop()
            if op=='local.tee':stack.append(env[int(t[1])])
        elif op in ('i32.and','i32.or','i32.xor'):
            b,a=stack.pop(),stack.pop();stack.append(node(op[4:],a,b))
        elif op in ('i32.rotl','i32.rotr'):
            b,a=stack.pop(),stack.pop()
            if b[0]!='c':raise ValueError('Constant rotates only')
            stack.append(node('rot',a,(b[1] if op.endswith('rotl') else -b[1])%32))
        else:raise ValueError('Unsupported source op '+op)
    for a in f[1:]:
        if a[0] not in ('type','param','local','result'):execute(a)
    if len(stack)!=1:raise ValueError('One final operand')
    if not nodes or stack[0]!=('s',len(nodes)-1):stack[-1]=node('copy',stack[-1])
    def pv(v):return var(v[1] if v[0]=='p' else n+v[1]) if v[0]!='c' else const(v[1])
    maps=[]
    for op,*args in nodes:
        a=pv(args[0])
        if op=='copy':z=a
        elif op=='rot':z=rotate(a,args[1])
        else:
            b=pv(args[1]);z=mul(a,b) if op=='and' else add(a,b)
            if op=='or':z=add(z,mul(a,b))
        maps.append(z)
    return n,maps,max(depth),nodes


def state_rank(maps,n,bit=False):
    coeff={};d=len(maps)
    for i,p in enumerate(maps):
        for m in p:
            if not any(v//32>=n for v in m):continue
            if not bit:coeff[m]=coeff.get(m,0)^(1<<i)
            else:
                for b in range(32):
                    k=tuple(sorted(set(32*(v//32)+(b-v%32)%32 for v in m)))
                    coeff[k]=coeff.get(k,0)^(1<<(32*i+b))
    return rank(coeff.values())


def construct(n,maps,depth,mode,seed):
    d=len(maps);rng=random.Random(seed);t=[1<<i for i in range(d)]
    targets=[i for i,p in enumerate(maps[:-1]) if not any(v//32>=n for m in p for v in m)]
    controls=[i for i in range(d-1) if i not in targets]
    pairs=[]
    if mode=='nonlinear':
        if len(controls)<2 or not targets:raise ValueError('Need source-only nodes and two untouched control coordinates')
        for j in targets:pairs.append((j,*rng.sample(controls,2)))
    if mode!='pipeline':
        for _ in range(3*d):
            dest=rng.randrange(d-1);src=rng.randrange(d)
            if src!=dest:t[dest]^=t[src]
    inv=inverse(t);state=[var(n+i) for i in range(d)];decoded=mix(inv,state)
    for j,a,b in pairs:decoded[j]=add(decoded[j],mul(decoded[a],decoded[b]))
    h=[sub(p,[var(i) for i in range(n)]+decoded) for p in maps]
    outer=list(h)
    for j,a,b in pairs:outer[j]=add(outer[j],mul(h[a],h[b]))
    h=mix(t,outer)
    rec={'n':n,'d':d,'depth':depth,'maps':[[list(m) for m in sorted(p)] for p in h]}
    return rec,{'linear':t,'inverse_linear':inv,'shears':pairs,'state_rank_word':state_rank(h,n),'state_rank_bit':state_rank(h,n,True),'terms':sum(map(len,h)),'degree':max([len(m) for p in h for m in p]+[0])}


def encode(r):
    monos=sorted({tuple(m) for p in r['maps'] for m in p});mi={m:i for i,m in enumerate(monos)}
    mo=[0];atoms=[]
    for m in monos:atoms.extend(m);mo.append(len(atoms))
    po=[0];indices=[]
    for p in r['maps']:indices.extend(mi[tuple(m)] for m in p);po.append(len(indices))
    words=[MAGIC,1,r['n'],r['d'],r['depth'],len(monos),len(atoms),len(indices)]+mo+atoms+po+indices
    return struct.pack('<'+'I'*len(words),*words)


def decode(data):
    words=list(struct.unpack('<'+'I'*(len(data)//4),data[:len(data)//4*4]));magic,version,n,d,depth,nm,na,ni=words[:8]
    if magic!=MAGIC or version!=1 or not(1<=n<=32 and 1<=d<=24 and 1<=depth<=24):raise ValueError('Bad descriptor')
    pos=8;mo=words[pos:pos+nm+1];pos+=nm+1;atoms=words[pos:pos+na];pos+=na;po=words[pos:pos+d+1];pos+=d+1;ids=words[pos:pos+ni]
    if len(ids)!=ni or mo[0]!=0 or mo[-1]!=na or po[0]!=0 or po[-1]!=ni:raise ValueError('Bad lengths')
    if mo!=sorted(mo) or po!=sorted(po) or any(v//32>=n+d for v in atoms) or any(i>=nm for i in ids):raise ValueError('Bad indices')
    monos=[atoms[mo[j]:mo[j+1]] for j in range(nm)]
    r={'n':n,'d':d,'depth':depth,'maps':[[monos[ids[k]] for k in range(po[j],po[j+1])] for j in range(d)]}
    if encode(r)!=data[:4*(pos+ni)]:raise ValueError('Noncanonical descriptor')
    return r


def layout(r):
    blob=encode(r);base=(len(blob)+63)//64*64;nm=struct.unpack_from('<I',blob,20)[0]
    args=base;old=base+4*r['n'];new=old+4*r['d'];cache=new+4*r['d'];end=cache+4*nm
    if end>65536*8:raise ValueError('Eight-page cap')
    return args,old,new,cache,end,(end+65535)//65536


def render(r):
    blob=encode(r);n,d,depth=r['n'],r['d'],r['depth'];args,old,new,cache,end,pages=layout(r)
    _,_,_,_,_,nm,na,ni=struct.unpack_from('<8I',blob)
    mo=32;atoms=mo+4*(nm+1);po=atoms+4*na;ids=po+4*(d+1)
    q=lambda o,i:f'(i32.load offset={o} (i32.shl {i} (i32.const 2)))'
    get=lambda j:f'(local.get ${j})'
    put=lambda off,i,v:f'(i32.store offset={off} (i32.shl {i} (i32.const 2)) {v})'
    loadmo=q(mo,get('m'));loadmo1=q(mo,f'(i32.add {get("m")} (i32.const 1))')
    text=''.join('\\%02x'%b for b in blob)
    init=''.join(put(args,f'(i32.const {i})',f'(local.get {i})') for i in range(n))
    return f'''(module (memory {pages} {pages}) (data (i32.const 0) "{text}")
    (func (export "run") (param {' '.join(['i32']*n)}) (result i32)
    (local $round i32) (local $m i32) (local $j i32) (local $end i32) (local $v i32) (local $a i32) (local $i i32)
    {init}
    (loop $rounds
      (local.set $m (i32.const 0))
      (block $monos_done (loop $monos
        (br_if $monos_done (i32.ge_u (local.get $m) (i32.const {nm})))
        (local.set $j {loadmo}) (local.set $end {loadmo1}) (local.set $v (i32.const -1))
        (block $factors_done (loop $factors
          (br_if $factors_done (i32.ge_u (local.get $j) (local.get $end)))
          (local.set $a {q(atoms,get('j'))})
          (local.set $v (i32.and (local.get $v) (i32.rotl
            {q(args,'(i32.shr_u (local.get $a) (i32.const 5))')}
            (i32.and (local.get $a) (i32.const 31)))))
          (local.set $j (i32.add (local.get $j) (i32.const 1))) (br $factors)))
        {put(cache,get('m'),get('v'))}
        (local.set $m (i32.add (local.get $m) (i32.const 1))) (br $monos)))
      (local.set $i (i32.const 0))
      (loop $outputs
        (local.set $j {q(po,get('i'))}) (local.set $end {q(po,'(i32.add (local.get $i) (i32.const 1))')})
        (local.set $v (i32.const 0))
        (block $sum_done (loop $sum
          (br_if $sum_done (i32.ge_u (local.get $j) (local.get $end)))
          (local.set $v (i32.xor (local.get $v) {q(cache,q(ids,get('j')))}))
          (local.set $j (i32.add (local.get $j) (i32.const 1))) (br $sum)))
        {put(new,get('i'),get('v'))}
        (local.set $i (i32.add (local.get $i) (i32.const 1))) (br_if $outputs (i32.lt_u (local.get $i) (i32.const {d}))))
      (memory.copy (i32.const {old}) (i32.const {new}) (i32.const {4*d}))
      (local.set $round (i32.add (local.get $round) (i32.const 1)))
      (br_if $rounds (i32.lt_u (local.get $round) (i32.const {depth}))))
    (i32.load (i32.const {old+4*(d-1)}))))'''


def save(text,dest):
    dest=Path(dest)
    if dest.exists() or dest.with_suffix('.wat').exists():raise FileExistsError(dest)
    dest.parent.mkdir(parents=True,exist_ok=True);dest.with_suffix('.wat').write_text(text,encoding='utf8')
    w.tool('wat2wasm',[dest.with_suffix('.wat'),'-o',dest]);w.tool('wasm-validate',[dest])


def transform(src,dest,mode='nonlinear',seed=20261023):
    start=time.perf_counter();n,maps,depth,nodes=source(src);r,meta=construct(n,maps,depth,mode,seed);save(render(r),dest)
    return {**meta,'n':n,'d':len(maps),'depth':depth,'elapsed_ms':(time.perf_counter()-start)*1000,'linear_memory_bytes':layout(r)[-1]*65536}


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');a.add_argument('--mode',choices=['pipeline','linear','nonlinear'],default='nonlinear');a.add_argument('--seed',type=int,default=20261023)
    q=a.parse_args();print(json.dumps(transform(q.input,q.output,q.mode,q.seed)))
