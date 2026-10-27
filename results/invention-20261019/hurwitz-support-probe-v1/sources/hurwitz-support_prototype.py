"""Support-bounded Hurwitz rewriting of public S5-valued factors.

Barrington compilation, Hurwitz moves and change of basis are known.
This prototype tests a generation heuristic, not cryptographic obfuscation.
"""
import argparse
from functools import lru_cache
import importlib.util
import itertools
import json
from pathlib import Path
import random
import time
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[2]
sp = importlib.util.spec_from_file_location('lane_common', ROOT/'research/lane-demand/prototype.py')
c = importlib.util.module_from_spec(sp); sp.loader.exec_module(c)
w = c.w
PERMS = list(itertools.permutations(range(5)))
IDS = {p:i for i,p in enumerate(PERMS)}
I = IDS[tuple(range(5))]
T = IDS[(1,2,3,4,0)]
M = [[IDS[tuple(a[b[i]] for i in range(5))] for b in PERMS] for a in PERMS]
INV = [next(j for j in range(120) if M[i][j] == I) for i in range(120)]
CYC = [i for i,p in enumerate(PERMS) if len({p[0],p[p[0]],p[p[p[0]]],p[p[p[p[0]]]],0})==5]
COMM = {}
for a in CYC:
    for b in CYC:
        k=M[M[M[a][b]][INV[a]]][INV[b]]
        if k in CYC and k not in COMM: COMM[k]=(a,b)
assert len(COMM)==24

class Factor(NamedTuple):
    support: tuple
    table: tuple

def factor(support, table):
    s=list(support);t=list(table)
    assert len(t)==1<<len(s) and s==sorted(set(s))
    for j in reversed(range(len(s))):
        if all(t[i]==t[i|(1<<j)] for i in range(len(t)) if not i&(1<<j)):
            t=[t[i] for i in range(len(t)) if not i&(1<<j)];s.pop(j)
    return Factor(tuple(s),tuple(t))

def value(f,x):
    key=sum(((x>>v)&1)<<j for j,v in enumerate(f.support))
    return f.table[key]

def mapped(f,fn): return factor(f.support,[fn(p) for p in f.table])

def combine(a,b):
    s=tuple(sorted(set(a.support+b.support)))
    t=[]
    for k in range(1<<len(s)):
        x=sum(((k>>j)&1)<<v for j,v in enumerate(s))
        t.append(M[value(a,x)][value(b,x)])
    return factor(s,t)

def inverse(word): return [mapped(f,lambda p:INV[p]) for f in reversed(word)]

def move(a,b,direction):
    if direction==0:
        return b,combine(combine(mapped(b,lambda p:INV[p]),a),b)
    return combine(combine(a,b),mapped(a,lambda p:INV[p])),a

def score(word): return sum(1<<len(f.support) for f in word)

def source(src):
    e=c.expanded(src)
    def bit(q):
        if q[0]!='i32.and': return None
        a,b=q[1:]
        if a[0]=='i32.const':a,b=b,a
        if b!=c.const(1):return None
        shift=0
        if a[0]=='i32.shr_u' and a[2][0]=='i32.const':
            shift=int(a[2][1])&31;a=a[1]
        if a[0]=='local.get' and a[1] in ('0','1'):return 32*int(a[1])+shift
        return None
    def walk(q):
        v=bit(q)
        if v is not None:return ('v',v)
        if q[0]=='i32.const' and int(q[1]) in (0,1):return ('c',int(q[1]))
        if q[0]=='i32.eqz':return ('not',walk(q[1]))
        if q[0] in ('i32.and','i32.or','i32.xor'):
            return (q[0][4:],walk(q[1]),walk(q[2]))
        raise ValueError('Expected a pure Boolean expression on explicit input bits: '+c.emit(q))
    return walk(e)

def formula_wat(t):
    op=t[0]
    if op=='v':
        v=t[1];return f'(i32.and (i32.shr_u (local.get {v//32}) (i32.const {v%32})) (i32.const 1))'
    if op=='c':return f'(i32.const {t[1]})'
    if op=='not':return '(i32.eqz '+formula_wat(t[1])+')'
    return f'(i32.{op} {formula_wat(t[1])} {formula_wat(t[2])})'

def eval_formula(t,x):
    op=t[0]
    if op=='v':return (x>>t[1])&1
    if op=='c':return t[1]
    if op=='not':return 1^eval_formula(t[1],x)
    a=eval_formula(t[1],x);b=eval_formula(t[2],x)
    return {'and':a&b,'or':a|b,'xor':a^b}[op]

def variables(t):
    if t[0]=='v':return {t[1]}
    if t[0]=='c':return set()
    return set().union(*(variables(q) for q in t[1:]))

def normalize(t):
    op=t[0]
    if op in ('v','c'):return t
    if op=='not':return ('not',normalize(t[1]))
    a,b=normalize(t[1]),normalize(t[2])
    if op=='and':return ('and',a,b)
    if op=='or':return ('not',('and',('not',a),('not',b)))
    return ('not',('and',('not',('and',a,('not',b))),('not',('and',('not',a),b))))

def barrington(t,limit=8192):
    @lru_cache(None)
    def go(t,target):
        op=t[0]
        if op=='v':return (factor((t[1],),(I,target)),)
        if op=='c':return (factor((),(target if t[1] else I,)),)
        if op=='not':
            word=list(go(t[1],INV[target]));word[-1]=mapped(word[-1],lambda p:M[p][target]);return tuple(word)
        a,b=COMM[target]
        left=go(t[1],a);right=go(t[2],b)
        if 2*(len(left)+len(right))>limit:raise ValueError('Branching program factor limit')
        return (*left,*right,*inverse(left),*inverse(right))
    return list(go(normalize(t),T))

def rewrite(word,seed=20261019,cap=3,attempts=None):
    rng=random.Random(seed);out=list(word);accepted=0
    for _ in range(attempts or 16*len(out)):
        if len(out)<2:break
        j=rng.randrange(len(out)-1);a,b=out[j:j+2]
        if len(set(a.support+b.support))>cap:continue
        pair=move(a,b,rng.randrange(2))
        if max(map(lambda f:len(f.support),pair))>cap:continue
        if score(pair)>=score((a,b)) and list(pair)!=[a,b]:
            out[j:j+2]=pair;accepted+=1
    return out,{'attempts':attempts or 16*len(out),'accepted':accepted}

def basis(word,seed):
    rng=random.Random(seed);rs=[I]+[rng.randrange(120) for _ in range(len(word)-1)]+[I]
    return [mapped(f,lambda p,j=j:M[M[INV[rs[j]]][p]][rs[j+1]]) for j,f in enumerate(word)]

def fuse(word,cap=3):
    out=[]
    for f in word:
        if out and len(set(out[-1].support+f.support))<=cap:out[-1]=combine(out[-1],f)
        else:out.append(f)
    return out

def wasm(word):
    data=bytearray();body=['(local.set 2 (v128.const i8x16 '+' '.join(map(str,range(16)))+'))']
    for f in word:
        offset=len(data)
        for p in f.table:data.extend((*PERMS[p],*range(5,16)))
        terms=[f'(i32.shl (i32.and (i32.shr_u (local.get {v//32}) (i32.const {v%32})) (i32.const 1)) (i32.const {j+4}))' for j,v in enumerate(f.support)]
        addr=f'(i32.const {offset})'
        for term in terms:addr=f'(i32.or {addr} {term})' if offset% (16<<len(f.support))==0 else f'(i32.add {addr} {term})'
        body.append(f'(local.set 2 (i8x16.swizzle (local.get 2) (v128.load {addr})))')
    body.append('(i32.ne (i8x16.extract_lane_u 0 (local.get 2)) (i32.const 0))')
    blob=''.join('\\%02x'%x for x in data)
    pages=max(1,(len(data)+65535)//65536)
    return '(module (memory '+str(pages)+' '+str(pages)+') (data (i32.const 0) "'+blob+'") (func (export "run") (param i32 i32) (result i32) (local v128) '+''.join(body)+'))'

def transform(src,dst,mode='braid',seed=20261019,cap=3):
    start=time.perf_counter();t=source(src);word=barrington(t);before=len(word);stats={}
    if mode=='braid':word,stats=rewrite(word,seed,cap)
    elif mode=='basis':word=basis(word,seed)
    elif mode=='fused':word=fuse(word,cap)
    elif mode!='base':raise ValueError(mode)
    c.compile_wat(wasm(word),dst)
    return dict(stats,mode=mode,factors=len(word),base_factors=before,entries=score(word),support_max=max(map(lambda f:len(f.support),word)),transform_ms=(time.perf_counter()-start)*1000)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['base','basis','fused','braid'],default='braid');ap.add_argument('--seed',type=int,default=20261019);ap.add_argument('--cap',type=int,choices=[1,2,3],default=3);a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode,a.seed,a.cap)))
