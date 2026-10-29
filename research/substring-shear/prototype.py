"""Restricted Wasm weighted grammar transformation and adaptive recovery.

All weights are modulo 2**32. Noncommutative monomials describe concatenation,
not products of the values in a single chart cell. No security claim.
"""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path
import struct
import tempfile
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('substring_common',HERE.parent/'mutation-quotient/prototype.py')
common=importlib.util.module_from_spec(s);s.loader.exec_module(common)
q=common.q
MASK=0xffffffff
MAGIC=0x31534743
CHART=4096
SIDE=33


def add(*ps):
    out={}
    for p in ps:
        for word,c in p.items():out[word]=(out.get(word,0)+c)&MASK
    return {w:c for w,c in out.items() if c}


def scale(p,c):return {w:(v*c)&MASK for w,v in p.items() if (v*c)&MASK}


def mul(p,q_):
    out={}
    for a,c in p.items():
        for b,d in q_.items():out[a+b]=(out.get(a+b,0)+c*d)&MASK
    return {w:c for w,c in out.items() if c}


def subst(p,images):
    out={}
    for word,c in p.items():
        term={():c}
        for x in word:term=mul(term,images[x] if x>=0 else {(x,):1})
        out=add(out,term)
    return out


def shear(ps,a,b,c,alpha,linear=False):
    # G=F(E^-1 Y)+(Y-E^-1 Y). E leaves b,c unchanged.
    n=len(ps)
    if not all(0<=i<n for i in (a,b,c)):raise ValueError('shear index bounds')
    if a==0 or a==b or (not linear and a==c):raise ValueError('invalid shear')
    word=(b,) if linear else (b,c)
    images=[{(i,):1} for i in range(n)]
    images[a]=add(images[a],{word:(-alpha)&MASK})
    out=[subst(p,images) for p in ps]
    out[a]=add(out[a],{word:alpha&MASK})
    if linear:
        # Linear term cancels by using E F(E^-1 Y), not the nonlinear formula.
        out=[subst(p,images) for p in ps]
        out[a]=add(out[a],scale(out[b],alpha))
    return out


def grammars():
    return [
        dict(name='dyck',alphabet=2,polys=[{(2,3):1,(2,1):1,(0,0):1},{(0,3):1},{(-1,):1},{(-2,):1}],a=1,b=2,c=0),
        dict(name='palindrome',alphabet=2,polys=[{(1,1):1,(2,2):1,(1,3):1,(2,4):1},{(-1,):1},{(-2,):1},{(0,1):1},{(0,2):1}],a=3,b=1,c=2),
        dict(name='expression',alphabet=3,polys=[{(-1,):1,(0,3):1,(0,4):1},{(-2,):1},{(-3,):1},{(1,0):1},{(2,0):1}],a=3,b=4,c=0),
    ]


def binarize(ps,alphabet):
    terminals=[];rules=[];n=len(ps);tails={}
    def tail(word):
        nonlocal n
        if len(word)==1:return word[0]
        if word in tails:return tails[word]
        a=n;n+=1;tails[word]=a
        rules.append((a,word[0],tail(word[1:]),1))
        return a
    for a,p in enumerate(ps):
        for word,c in sorted(p.items()):
            if len(word)==1 and word[0]<0:terminals.append((a,-word[0]-1,c))
            elif len(word)>=2 and all(x>=0 for x in word):rules.append((a,word[0],tail(word[1:]),c))
            else:raise ValueError('proper nonempty grammar required')
    return dict(n=n,alphabet=alphabet,terminals=sorted(terminals),rules=sorted(rules))


def expand(g,d):
    n=g['n'];ps=[{} for _ in range(n)]
    for a,t,c in g['terminals']:ps[a]=add(ps[a],{(-t-1,):c})
    for a,b,c,w in g['rules']:ps[a]=add(ps[a],{(b,c):w})
    cache={};visiting=set()
    def image(i):
        if i<d:return {(i,):1}
        if i in cache:return cache[i]
        if i in visiting or len(ps[i])!=1:raise ValueError('not a single acyclic suffix definition')
        word,w=next(iter(ps[i].items()))
        if w!=1 or len(word)!=2 or min(word)<0:raise ValueError('not a binary unit definition')
        visiting.add(i);value=mul(image(word[0]),image(word[1]));visiting.remove(i)
        cache[i]=value;return value
    images=[image(i) for i in range(n)]
    return [subst(p,images) for p in ps[:d]]


def render(g):
    n=g['n'];nt=len(g['terminals']);nr=len(g['rules']);alphabet=g['alphabet']
    if not 2<=n<=48 or not 1<=alphabet<=4:raise ValueError('grammar bounds')
    for a,t,c in g['terminals']:
        if not 0<=a<n or not 0<=t<alphabet or not 0<c<=MASK:raise ValueError('terminal')
    for a,b,c,w in g['rules']:
        if not all(0<=i<n for i in (a,b,c)) or not 0<w<=MASK:raise ValueError('rule')
    data=struct.pack('<5I',MAGIC,n,alphabet,nt,nr)+bytes(44)
    for t in g['terminals']:data+=struct.pack('<3I',*t)
    for r in g['rules']:data+=struct.pack('<4I',*r)
    if len(data)>CHART:raise ValueError('rule table too large')
    pages=(CHART+SIDE*SIDE*n*4+65535)//65536
    # Params low,high,length. Locals i,len,end,k,r,p,addr,value,symbol.
    return f'''(module (memory {pages} {pages}) (data (i32.const 0) {common.token(data)})
      (func $cell (param i32 i32 i32) (result i32)
        (i32.add (i32.const {CHART}) (i32.shl
          (i32.add (i32.mul (i32.add (i32.mul (local.get 0) (i32.const {SIDE})) (local.get 1)) (i32.const {n})) (local.get 2)) (i32.const 2))))
      (func $symbol (param i32 i32 i32) (result i32)
        (i32.and (i32.shr_u
          (if (result i32) (i32.lt_u (local.get 2) (i32.const 16)) (then (local.get 0)) (else (local.get 1)))
          (i32.shl (local.get 2) (i32.const 1))) (i32.const 3)))
      (func $run (export "run") (param i32 i32 i32) (result i32)
        (local i32 i32 i32 i32 i32 i32 i32 i32 i32)
        (if (i32.gt_u (local.get 2) (i32.const 32)) (then unreachable))
        (if (i32.eqz (local.get 2)) (then (return (i32.const 0))))
        (loop $validate
          (if (i32.ge_u (call $symbol (local.get 0) (local.get 1) (local.get 3)) (i32.const {alphabet})) (then unreachable))
          (local.set 3 (i32.add (local.get 3) (i32.const 1)))
          (br_if $validate (i32.lt_u (local.get 3) (local.get 2))))
        (memory.fill (i32.const {CHART}) (i32.const 0) (i32.const {SIDE*SIDE*n*4}))
        (local.set 3 (i32.const 0))
        (loop $leaves
          (local.set 11 (call $symbol (local.get 0) (local.get 1) (local.get 3)))
          (local.set 7 (i32.const 0))
          (block $terminal_end (loop $terminal
            (br_if $terminal_end (i32.ge_u (local.get 7) (i32.const {nt})))
            (local.set 8 (i32.add (i32.const 64) (i32.mul (local.get 7) (i32.const 12))))
            (if (i32.eq (local.get 11) (i32.load offset=4 (local.get 8))) (then
              (local.set 9 (call $cell (local.get 3) (i32.add (local.get 3) (i32.const 1)) (i32.load (local.get 8))))
              (i32.store (local.get 9) (i32.add (i32.load (local.get 9)) (i32.load offset=8 (local.get 8))))))
            (local.set 7 (i32.add (local.get 7) (i32.const 1))) (br $terminal)))
          (local.set 3 (i32.add (local.get 3) (i32.const 1)))
          (br_if $leaves (i32.lt_u (local.get 3) (local.get 2))))
        (local.set 4 (i32.const 2))
        (block $length_end (loop $length
          (br_if $length_end (i32.gt_u (local.get 4) (local.get 2)))
          (local.set 3 (i32.const 0))
          (loop $start
            (local.set 5 (i32.add (local.get 3) (local.get 4)))
            (local.set 6 (i32.add (local.get 3) (i32.const 1)))
            (loop $split
              (local.set 7 (i32.const 0))
              (block $rule_end (loop $rule
                (br_if $rule_end (i32.ge_u (local.get 7) (i32.const {nr})))
                (local.set 8 (i32.add (i32.const {64+12*nt}) (i32.shl (local.get 7) (i32.const 4))))
                (local.set 9 (call $cell (local.get 3) (local.get 5) (i32.load (local.get 8))))
                (local.set 10 (i32.mul (i32.load offset=12 (local.get 8))
                  (i32.mul (i32.load (call $cell (local.get 3) (local.get 6) (i32.load offset=4 (local.get 8))))
                           (i32.load (call $cell (local.get 6) (local.get 5) (i32.load offset=8 (local.get 8)))))))
                (i32.store (local.get 9) (i32.add (i32.load (local.get 9)) (local.get 10)))
                (local.set 7 (i32.add (local.get 7) (i32.const 1))) (br $rule)))
              (local.set 6 (i32.add (local.get 6) (i32.const 1)))
              (br_if $split (i32.lt_u (local.get 6) (local.get 5))))
            (local.set 3 (i32.add (local.get 3) (i32.const 1)))
            (br_if $start (i32.le_u (i32.add (local.get 3) (local.get 4)) (local.get 2))))
          (local.set 4 (i32.add (local.get 4) (i32.const 1))) (br $length)))
        (i32.load (call $cell (i32.const 0) (local.get 2) (i32.const 0)))))'''


def read(src):
    m=q.read(src);data=bytearray(4096)
    for e in m[1:]:
        if e[0]=='data':
            if e[1][0]!='i32.const':raise ValueError('active constant data required')
            off=int(e[1][1]);b=b''.join(common.decode(x) for x in e[2:])
            if off<0 or off+len(b)>len(data):raise ValueError('data bounds')
            data[off:off+len(b)]=b
    magic,n,alphabet,nt,nr=struct.unpack_from('<5I',data)
    if magic!=MAGIC or not 2<=n<=48 or nt*12+nr*16>4032:raise ValueError('header')
    g=dict(n=n,alphabet=alphabet,terminals=[struct.unpack_from('<3I',data,64+12*i) for i in range(nt)],
           rules=[struct.unpack_from('<4I',data,64+12*nt+16*i) for i in range(nr)])
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as td:
        raw=Path(td)/'profile.wasm';q.compile(render(g),raw)
        if q.read(raw)!=m:
            opt=Path(td)/'profile-opt.wasm';q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',opt])
            if q.read(opt)!=m:raise ValueError('not the exact validated raw/O3 profile')
    return g


def transform(src,dst,a,b,c,alpha,linear=False):
    t=time.perf_counter();g=read(src);ps=expand(g,g['n'])
    out=binarize(shear(ps,a,b,c,alpha,linear),g['alphabet']);q.compile(render(out),dst)
    return dict(ms=(time.perf_counter()-t)*1000,n=out['n'],rules=len(out['rules']))


def lowdegree(ps):
    return all(len(w)==2 and min(w)>=0 or len(w)==1 and w[0]<0 for p in ps for w in p)


def cubic_candidates(ps,a,b,c):
    """Solve every cubic coefficient of inverse shear, affine in alpha.

    Returns one congruence alpha=residue mod modulus. Full polynomial checking
    follows. For a genuine single shear of a binary grammar, its least residue
    already removes the quartic part too; no enumeration of lifts is required.
    """
    zero=shear(ps,a,b,c,0);one=shear(ps,a,b,c,-1)
    residue=0;modulus=1
    for p0,p1 in zip(zero,one):
        for word in set(p0)|set(p1):
            if len(word)!=3:continue
            intercept=p0.get(word,0);slope=(p1.get(word,0)-intercept)&MASK
            target=(-intercept)&MASK
            if not slope:
                if target:return None
                continue
            factor=slope&-slope
            if target%factor:return None
            mod=(1<<32)//factor
            r=((target//factor)*pow(slope//factor,-1,mod))%mod
            if (r-residue)%min(mod,modulus):return None
            if mod>modulus:residue,modulus=r,mod
    return residue,modulus


def recover(src,dst,linear=False,weighted=False):
    t=time.perf_counter();g=read(src);read_ms=(time.perf_counter()-t)*1000;t=time.perf_counter()
    attempts=0;candidates=[];prefixes=0
    for d in range(2,g['n']+1):
        try:ps=expand(g,d)
        except ValueError:continue
        if any(len(word)>4 for p in ps for word in p):continue
        prefixes+=1
        for a in range(1,d):
            for b in range(d):
                if b==a:continue
                for c in ([b] if linear else range(d)):
                    if c==a:continue
                    if weighted:
                        if linear:raise ValueError('weighted linear recovery is not implemented')
                        solved=cubic_candidates(ps,a,b,c)
                        if solved is None:continue
                        residue,modulus=solved
                        alphas={residue}
                    elif linear:
                        # Coefficients of modified equation are u + alpha*v,
                        # with source u,v in {0,1}. Enumerate observed c,c-1.
                        alphas={v& MASK for value in ps[a].values() for v in (value,value-1)}
                    else:
                        v=ps[a].get((b,c),0);alphas={v,(v-1)&MASK}
                    for alpha in sorted(alphas if weighted else alphas-{0}):
                        attempts+=1;candidate=shear(ps,a,b,c,(-alpha)&MASK,linear)
                        if not lowdegree(candidate) or (not weighted and any(v!=1 for p in candidate for v in p.values())):continue
                        # Full polynomial identity, not an I/O guess.
                        if shear(candidate,a,b,c,alpha,linear)!=ps:raise AssertionError('inverse identity')
                        cg=binarize(candidate,g['alphabet'])
                        candidates.append((len(cg['rules'])+len(cg['terminals']),d,a,b,c,alpha,cg))
    search_ms=(time.perf_counter()-t)*1000
    if not candidates:return dict(status='no_candidate',read_ms=read_ms,search_ms=search_ms,attempts=attempts)
    candidates.sort(key=lambda x:x[:-1]);_,d,a,b,c,alpha,out=candidates[0]
    q.compile(render(out),dst)
    return dict(status='recovered',read_ms=read_ms,search_ms=search_ms,attempts=attempts,
                candidates=len(candidates),a=a,b=b,c=c,alpha=alpha,n=out['n'],rules=len(out['rules']),
                prefixes=prefixes,total_ms=(time.perf_counter()-t)*1000+read_ms)


if __name__=='__main__':
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    a=sp.add_parser('transform');a.add_argument('source');a.add_argument('output');a.add_argument('--a',type=int,required=True);a.add_argument('--b',type=int,required=True);a.add_argument('--c',type=int,required=True);a.add_argument('--alpha',type=int,required=True);a.add_argument('--linear',action='store_true')
    a=sp.add_parser('recover');a.add_argument('source');a.add_argument('output');a.add_argument('--linear',action='store_true');a.add_argument('--weighted',action='store_true')
    a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.a,a.b,a.c,a.alpha,a.linear) if a.cmd=='transform' else recover(a.source,a.output,a.linear,a.weighted)))
