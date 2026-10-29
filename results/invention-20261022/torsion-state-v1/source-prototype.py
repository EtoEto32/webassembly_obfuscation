"""Non-injective state representation and public-response recurrence recovery.

Not an assertion of a new obfuscation primitive. All arithmetic is modulo 2**32.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('torsion_wat',HERE.parent/'connectivity-elimination/prototype.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
BITS=32;MOD=1<<BITS;MASK=MOD-1


def ident(n):return [[int(i==j) for j in range(n)] for i in range(n)]
def mul(a,b):return [[sum(x*y for x,y in zip(row,col))&MASK for col in zip(*b)] for row in a]
def vec(a,b):return [sum(x*y for x,y in zip(row,b))&MASK for row in a]
def diag(xs):return [[x if i==j else 0 for j in range(len(xs))] for i,x in enumerate(xs)]


def sum_wat(terms):
    if not terms:return '(i32.const 0)'
    s=terms[0]
    for t in terms[1:]:s=f'(i32.add {s} {t})'
    return s


def dot_wat(coeff,values):
    return sum_wat([v if c==1 else f'(i32.mul (i32.const {c}) {v})' for c,v in zip(coeff,values) if c])


def emit(a,b,c):
    n=len(a);body=[]
    for i in range(n):
        v=dot_wat(a[i]+[b[i]],[f'(global.get {j})' for j in range(n)]+['(local.get 0)'])
        body.append(f'(local.set {i+1} {v})')
    body += [f'(global.set {i} (local.get {i+1}))' for i in range(n)]
    body.append(dot_wat(c,[f'(global.get {j})' for j in range(n)]))
    return ('(module '+' '.join('(global (mut i32) (i32.const 0))' for _ in range(n))+
            ' (func (export "step") (param i32) (result i32) (local '+' '.join(['i32']*n)+') '+' '.join(body)+')'+
            ' (func (export "reset") '+' '.join(f'(global.set {i} (i32.const 0))' for i in range(n))+'))')


def save(text,out):
    out=Path(out)
    if out.exists() or out.with_suffix('.wat').exists():raise FileExistsError(out)
    out.parent.mkdir(parents=True,exist_ok=True);out.with_suffix('.wat').write_text(text,encoding='utf8')
    w.tool('wat2wasm',[out.with_suffix('.wat'),'-o',out]);w.tool('wasm-validate',[out])


def linear(x,n):
    if x[0]=='i32.const':return [0]*(n+1)+[int(x[1])&MASK]
    if x[0]=='global.get' and 0<=int(x[1])<n:
        v=[0]*(n+2);v[int(x[1])]=1;return v
    if x==['local.get','0']:
        return [0]*n+[1,0]
    if x[0]=='i32.add':return [(a+b)&MASK for a,b in zip(linear(x[1],n),linear(x[2],n))]
    if x[0]=='i32.mul':
        a,b=linear(x[1],n),linear(x[2],n)
        if any(a[:-1]) and any(b[:-1]):raise ValueError('Nonlinear expression')
        if any(a[:-1]):a,b=b,a
        return [(a[-1]*v)&MASK for v in b]
    raise ValueError('Nonlinear or unsupported expression: '+w.emit(x))


def source(path):
    w.tool('wasm-validate',[path]);m=w.parse(w.tool('wasm2wat',[path,'--fold-exprs']))
    if any(x[0] not in ('type','global','func','export') for x in m[1:]):raise ValueError('Unsupported module section')
    gs=[x for x in m[1:] if x[0]=='global'];fs=[x for x in m[1:] if x[0]=='func'];n=len(gs)
    if not 2<=n<=8 or gs!=[['global',['mut','i32'],['i32.const','0']] for _ in range(n)]:raise ValueError('Expected 2..8 private zero i32 globals')
    exports=[x for x in m[1:] if x[0]=='export']
    if sorted(w.emit(x) for x in exports)!=sorted(['(export "step" (func 0))','(export "reset" (func 1))']) or len(fs)!=2:raise ValueError('Exports/functions')
    f=fs[0];params=[x for x in f[1:] if isinstance(x,list) and x[0]=='param'];res=[x for x in f[1:] if isinstance(x,list) and x[0]=='result'];loc=[v for x in f[1:] if isinstance(x,list) and x[0]=='local' for v in x[1:]]
    if params!=[['param','i32']] or res!=[['result','i32']] or loc!=['i32']*n:raise ValueError('Step signature/locals')
    body=[x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','result','local')]
    if len(body)!=2*n+1:raise ValueError('Step body shape')
    a=[];b=[]
    for i in range(n):
        x=body[i]
        if len(x)!=3 or x[:2]!=['local.set',str(i+1)]:raise ValueError('Expected simultaneous temporary definitions')
        v=linear(x[2],n)
        if v[-1]:raise ValueError('Affine bias unsupported')
        a.append(v[:n]);b.append(v[n])
    if body[n:2*n]!=[['global.set',str(i),['local.get',str(i+1)]] for i in range(n)]:raise ValueError('Update order')
    out=linear(body[-1],n)
    if any(out[n:]):raise ValueError('Output input/bias unsupported')
    reset=[x for x in fs[1][1:] if isinstance(x,list) and x[0]!='type']
    if reset!=[['global.set',str(i),['i32.const','0']] for i in range(n)]:raise ValueError('Reset')
    return a,b,out[:n]


def basis(n,seed):
    r=random.Random(seed);u=ident(n);inv=ident(n)
    for k in range(4*n):
        i,j=r.sample(range(n),2);a=r.getrandbits(32)|1
        # left multiplication by elementary shear; inverse right multiplication.
        u[i]=[(x+a*y)&MASK for x,y in zip(u[i],u[j])]
        for row in inv:row[j]=(row[j]-a*row[i])&MASK
    assert mul(u,inv)==ident(n)==mul(inv,u)
    return u,inv


def transform(src,out,shifts,mode,seed=20261022):
    start=time.perf_counter();a,b,c=source(src);n=len(a)
    if len(shifts)!=n or any(not 0<=s<32 for s in shifts):raise ValueError('Shifts')
    u,inv=basis(n,seed)
    if mode=='basis':shifts=[0]*n
    d=diag([1<<s for s in shifts]);g=[]
    for i in range(n):
        row=[]
        for j in range(n):
            k=shifts[j]-shifts[i]
            if k>0 and a[i][j]%(1<<k):raise ValueError('Kernel not preserved by A')
            row.append(((a[i][j]>>k) if k>0 else (a[i][j]<<(-k)))&MASK)
        g.append(row)
    h=[]
    for x,s in zip(c,shifts):
        if x%(1<<s):raise ValueError('Output does not annihilate kernel')
        h.append(x>>s)
    perturb=[[0]*n for _ in range(n)]
    if mode in ('perturb','bad'):
        rng=random.Random(seed+91)
        for i in range(n):
            for j,s in enumerate(shifts):
                if s:
                    exponent=32-s-(1 if mode=='bad' and i==0 and j==next(k for k,v in enumerate(shifts) if v) else 0)
                    perturb[i][j]=((rng.getrandbits(32)|1)<<exponent)&MASK
    gp=[[(v+k)&MASK for v,k in zip(row,kr)] for row,kr in zip(g,perturb)]
    aa=mul(mul(u,gp),inv);bb=vec(u,vec(d,b));cc=mul([h],inv)[0];e=mul(u,d)
    certificates={'transition':mul(aa,e)==mul(e,a),'input':bb==vec(e,b),'output':mul([cc],e)[0]==c,
                  'annihilator':mul(perturb,d)==[[0]*n for _ in range(n)]}
    if mode!='bad' and not all(certificates.values()):raise AssertionError('Certificate')
    save(emit(aa,bb,cc),out)
    return {'mode':mode,'n':n,'shifts':shifts,'seed':seed,'certificate':certificates,
            'ambient_kernel_log2_size':sum(shifts),'image_log2_size':32*n-sum(shifts),'elapsed_ms':1000*(time.perf_counter()-start)}


def valuation(x,bits=32):return bits if not x else (x&-x).bit_length()-1


def solve(matrix,rhs,columns,bits=32):
    """One solution over Z/(2**bits), or None. Smallest-valuation pivot.

    Invert only odd factors. Track column operations for original unknowns.
    This is modular diagonal elimination, not field Gaussian elimination.
    """
    mod=1<<bits;mask=mod-1
    a=[[v&mask for v in row] for row in matrix];b=[v&mask for v in rhs]
    rows=len(a);n=columns;v=[[int(i==j) for j in range(n)] for i in range(n)];pivots=[];k=0
    while k<min(rows,n):
        options=[(valuation(a[i][j],bits),i,j) for i in range(k,rows) for j in range(k,n) if a[i][j]]
        if not options:break
        power,i,j=min(options);a[k],a[i]=a[i],a[k];b[k],b[i]=b[i],b[k]
        for row in a:row[k],row[j]=row[j],row[k]
        for row in v:row[k],row[j]=row[j],row[k]
        inv=pow(a[k][k]>>power,-1,mod)
        a[k]=[(x*inv)&mask for x in a[k]];b[k]=(b[k]*inv)&mask
        for i in range(k+1,rows):
            q=a[i][k]>>power
            a[i]=[(x-q*y)&mask for x,y in zip(a[i],a[k])];b[i]=(b[i]-q*b[k])&mask
        for j in range(k+1,n):
            q=a[k][j]>>power
            for i in range(rows):a[i][j]=(a[i][j]-q*a[i][k])&mask
            for i in range(n):v[i][j]=(v[i][j]-q*v[i][k])&mask
        pivots.append(power);k+=1
    y=[0]*n
    for i,s in enumerate(pivots):
        if b[i]%(1<<s):return None
        y[i]=b[i]>>s
    if any(b[i] for i in range(k,rows)):return None
    x=[sum(q*z for q,z in zip(row,y))&mask for row in v]
    if any(sum(q*z for q,z in zip(row,x))&mask != (wanted&mask) for row,wanted in zip(matrix,rhs)):
        raise AssertionError('Solver residual')
    return {'solution':x,'pivot_valuations':pivots,'free_variables':n-k}


def recurrence(samples,bound,bits=32):
    mask=(1<<bits)-1
    if len(samples)!=2*bound:raise ValueError('Need exactly 2N samples')
    if not any(samples):return {'order':0,'feedback':[],'numerator':[],'solver':None}
    for order in range(1,bound+1):
        rows=[[samples[t-1-i] for i in range(order)] for t in range(order,len(samples))]
        result=solve(rows,samples[order:],order,bits)
        if result is None:continue
        a=result['solution'];b=[(samples[j]-sum(a[i-1]*samples[j-i] for i in range(1,j+1)))&mask for j in range(order)]
        return {'order':order,'feedback':a,'numerator':b,'solver':result}
    raise ValueError('No recurrence within promise bound')


def emit_recurrence(model):
    r=model['order'];a=model['feedback'];b=model['numerator']
    if not r:return '(module (func (export "step") (param i32) (result i32) (i32.const 0)) (func (export "reset")))'
    # r past outputs and r-1 past inputs. Compute before shifting histories.
    value=dot_wat(a,[f'(global.get {i})' for i in range(r)])
    value=f'(i32.add {value} {dot_wat(b,["(local.get 0)"]+[f"(global.get {r+i})" for i in range(r-1)])})'
    body=[f'(local.set 1 {value})']
    body += [f'(global.set {i} (global.get {i-1}))' for i in range(r-1,0,-1)]
    body += ['(global.set 0 (local.get 1))']
    body += [f'(global.set {r+i} (global.get {r+i-1}))' for i in range(r-2,0,-1)]
    if r>1:body += [f'(global.set {r} (local.get 0))']
    body += ['(local.get 1)'];n=2*r-1
    return '(module '+' '.join('(global (mut i32) (i32.const 0))' for _ in range(n))+' (func (export "step") (param i32) (result i32) (local i32) '+' '.join(body)+') (func (export "reset") '+' '.join(f'(global.set {i} (i32.const 0))' for i in range(n))+'))'


def recover(src,out,bound=8):
    start=time.perf_counter()
    result=subprocess.run(['node',str(HERE/'query.cjs'),str(src),str(bound)],capture_output=True,text=True,timeout=30,check=True)
    query=json.loads(result.stdout);sample_ms=1000*(time.perf_counter()-start)
    t=time.perf_counter();model=recurrence(query['values'],bound);fit_ms=1000*(time.perf_counter()-t)
    save(emit_recurrence(model),out)
    return {'bound':bound,'query':query,'model':model,'query_ms':sample_ms,'fit_ms':fit_ms,'elapsed_ms':1000*(time.perf_counter()-start)}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['basis','quotient','perturb','bad','recover']);p.add_argument('source');p.add_argument('output');p.add_argument('--shifts',default='0,8,16');p.add_argument('--seed',type=int,default=20261022);p.add_argument('--bound',type=int,default=8);args=p.parse_args()
    result=recover(args.source,args.output,args.bound) if args.action=='recover' else transform(args.source,args.output,list(map(int,args.shifts.split(','))),args.action,args.seed)
    print(json.dumps(result,indent=2))
