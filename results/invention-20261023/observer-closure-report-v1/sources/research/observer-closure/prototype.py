"""Restricted polynomial observable-state compiler; no novelty claim."""
import argparse, importlib.util, json, math, subprocess, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('observer_poly',ROOT/'research/dyadic-difference/prototype.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
q=d.q
MASK=(1<<32)-1

def valuation(c,w=32):
    c %= 1<<w
    return (c&-c).bit_length()-1 if c else w

def product(a,b,w):
    mask=(1<<w)-1;out={}
    for (i,j),v in a.items():
        for (k,l),t in b.items():out[i+k,j+l]=(out.get((i+k,j+l),0)+v*t)&mask
    return {k:v for k,v in out.items() if v}

def powers(coeff,maxj,w):
    mask=(1<<w)-1;f={(i,0):c&mask for i,c in enumerate(coeff) if c&mask};f[0,1]=1
    rows=[{(0,0):1}]
    for _ in range(maxj):rows.append(product(rows[-1],f,w))
    return rows

def closure(coeff,w=32,full=False,cap=64):
    """Least requirements by coefficient divisibility, not by function identity."""
    e={2:0}
    if full:e[1]=0
    cache={};rounds=0
    def power(j):
        if j not in cache:cache[j]=powers(coeff,j,w)[-1]
        return cache[j]
    while True:
        before=dict(e);rounds+=1
        for j,ej in list(e.items()):
            for (k,l),c in power(j).items():
                v=min(w,ej+valuation(c,w))
                if k and v<w:
                    if k>cap:raise ValueError('closure degree cap exceeded')
                    e[k]=min(e.get(k,w),v)
        if before==e:break
        if rounds>w*(cap+1):raise AssertionError('nonmonotone worklist')
    e=dict(sorted(e.items()));updates={};mask=(1<<w)-1
    for j,ej in e.items():
        terms=[]
        for (k,l),c in sorted(power(j).items()):
            c=(c<<ej)&mask
            if not c:continue
            ek=e[k] if k else 0
            if c%(1<<ek):raise AssertionError('nondivisible closure')
            terms.append((k,l,c>>ek))
        updates[j]=terms
    return e,updates,rounds

def c(x):return '(i32.const %d)'%(x&MASK)
def add(a,b):return '(i32.add '+a+' '+b+')'
def mul(a,b):return '(i32.mul '+a+' '+b+')'
def power_expr(x,n):
    if n==0:return c(1)
    if n==1:return x
    h=power_expr(x,n//2);v=mul(h,h)
    return mul(v,x) if n%2 else v
def sum_expr(terms):
    if not terms:return c(0)
    v=terms[0]
    for t in terms[1:]:v=add(v,t)
    return v
def source(coeff):
    x='(global.get 0)'
    return '''(module (global (mut i32) (i32.const 0))
      (func (export "reset") (param i32) (global.set 0 (local.get 0)))
      (func (export "peek") (result i32) '''+mul(x,x)+''')
      (func (export "step") (param i32) (result i32)
       (global.set 0 '''+add(d.horner(coeff,x),'(local.get 0)')+') '+mul(x,x)+'))'

def parse(src):
    m=q.read(src)
    if any(v[0] not in ('type','func','global','export') for v in m[1:]):raise ValueError('closed globals-only profile')
    fs=[v for v in m[1:] if v[0]=='func'];gs=[v for v in m[1:] if v[0]=='global']
    if len(fs)!=3 or gs!=[['global',['mut','i32'],['i32.const','0']]]:raise ValueError('three functions / one zero state')
    body=[v for v in fs[2][1:] if v[0] not in ('type','param','result')]
    if len(body)!=2 or body[0][:2]!=['global.set','0'] or body[0][2][0]!='i32.add' or body[0][2][2]!=['local.get','0']:raise ValueError('F(x)+u update required')
    def replace(e):
        if e==['global.get','0']:return ['local.get','0']
        if e[0] not in ('i32.add','i32.sub','i32.mul','i32.const'):raise ValueError('polynomial only')
        return [e[0],*[replace(t) if isinstance(t,list) else t for t in e[1:]]]
    expr=replace(body[0][2][1]);coeff=d.polynomial(['func',['param','i32'],['result','i32'],expr])
    if not 2<=len(coeff)-1<=4:raise ValueError('degree 2..4 profile')
    with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='observer-source-') as td:
        ref=Path(td)/'source.wasm';q.compile(source(coeff),ref)
        if q.read(ref)!=m:raise ValueError('source outside canonical complete profile')
    return coeff

def emitted(coeff,full=False,bad=False):
    e,updates,rounds=closure(coeff,full=full);keys=list(e);idx={j:i for i,j in enumerate(keys)}
    globals_=' '.join('(global (mut i32) (i32.const 0))' for j in keys)
    reset=' '.join('(global.set %d %s)'%(idx[j],mul(c(1<<e[j]),power_expr('(local.get 0)',j))) for j in keys)
    step=[]
    for j in keys:
        terms=[]
        for k,l,coef in updates[j]:
            if bad and k==1:continue
            t=power_expr('(local.get 0)',l)
            if k:t=mul('(global.get %d)'%idx[k],t)
            if coef!=1:t=mul(c(coef),t)
            terms.append(t)
        step.append('(local.set %d %s)'%(idx[j]+1,sum_expr(terms)))
    step+=['(global.set %d (local.get %d))'%(idx[j],idx[j]+1) for j in keys]
    out='(module '+globals_+' (func (export "reset") (param i32) '+reset+') (func (export "peek") (result i32) (global.get %d))'%idx[2]
    out+=' (func (export "step") (param i32) (result i32) (local '+' '.join('i32' for _ in keys)+') '+' '.join(step)+' (global.get %d)))'%idx[2]
    return out,{'exponents':e,'updates':updates,'worklist_rounds':rounds,'state_words':len(e),'retains_unscaled_x':e.get(1)==0}

def transform(src,dst,mode='quotient'):
    start=time.perf_counter();coeff=parse(src);read=time.perf_counter()
    text,info=emitted(coeff,mode=='full',mode=='bad');build=time.perf_counter();q.compile(text,dst)
    return {**info,'mode':mode,'read_ms':(read-start)*1000,'build_ms':(build-read)*1000,'transform_ms':(time.perf_counter()-start)*1000}

def interpolate(values,w):
    """Canonical falling-factorial interpolation modulo 2**w."""
    modulus=1<<w;v=[a%modulus for a in values];basis=[1];answer=[0]*len(v);steps=[]
    for k in range(len(values)):
        fact=math.factorial(k);r=valuation(fact,w)
        if r>=w:raise ValueError('insufficient interpolation precision')
        if v[0]%(1<<r):raise ValueError('not an integer polynomial profile')
        ck=((v[0]>>r)*pow(fact>>r,-1,1<<(w-r)))%(1<<(w-r))
        if k:
            new=[0]*(len(basis)+1)
            for i,a in enumerate(basis):new[i]-=(k-1)*a;new[i+1]+=a
            basis=new
        for i,a in enumerate(basis):answer[i]=(answer[i]+ck*a)%modulus
        steps.append({'degree':k,'difference':v[0],'factorial_v2':r,'coefficient':ck})
        v=[(v[i+1]-v[i])%modulus for i in range(len(v)-1)]
    return d.trim(answer),steps

def step_only(text):
    return text.replace('(export "reset")','').replace('(export "peek")','')

def recover(src,dst,fresh=False):
    """Only binary execution and fixed public degree bound; no source metadata."""
    start=time.perf_counter()
    r=subprocess.run(['node',str(HERE/'query.cjs'),str(Path(src).resolve()),'fresh' if fresh else 'reset'],capture_output=True,text=True,timeout=30)
    if r.returncode:raise ValueError('query failed: '+r.stderr)
    obs=json.loads(r.stdout);queried=time.perf_counter();vals=[]
    for row in obs['samples']:
        diff=(row['one']-row['zero']-1)&MASK
        if diff&1:raise ValueError('square observer difference must be even')
        vals.append(diff>>1)
    coeff,steps=interpolate(vals,31);learned=time.perf_counter();q.compile(step_only(source(coeff)) if fresh else source(coeff),dst)
    return {'status':'candidate_recovered','fresh':fresh,'bootstrap':obs.get('bootstrap'),'degree_bound':4,'coefficients_mod_2_31':coeff,'query_calls':obs['calls'],'samples':obs['samples'],'interpolation':steps,'query_ms':(queried-start)*1000,'interpolation_ms':(learned-queried)*1000,'total_ms':(time.perf_counter()-start)*1000,'certification':'conditional on the public source profile; finite queries alone do not certify arbitrary Wasm'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('source');ap.add_argument('output');ap.add_argument('--mode',choices=['quotient','full','bad'],default='quotient');ap.add_argument('--fresh',action='store_true');a=ap.parse_args()
    result=transform(a.source,a.output,a.mode) if a.action=='transform' else recover(a.source,a.output,a.fresh)
    q.save(str(a.output)+'.json',result);print(json.dumps(result))
