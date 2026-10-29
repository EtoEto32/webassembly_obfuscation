"""Exact-profile symmetric-state compiler and public-polynomial lifting attack."""
import argparse, hashlib, json, sys, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/observation-synthesis'))
sys.path.insert(0,str(ROOT/'.tools/nonbijective-residual-cas'))
import transform as wasm
import sympy as sp
x,y,z=sp.symbols('x y z');MASK=2**32-1

def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return wasm.parse(wasm.tool('wasm2wat',[p,'--fold-exprs']))
def items(m,k):return [v for v in m if isinstance(v,list) and v[0]==k]
def decl(v):return isinstance(v,list) and v[0] in ('type','param','result','local','export')
def body(f):return [v for v in f[1:] if not decl(v)]
def nodes(v):
    if isinstance(v,list):
        yield v
        for c in v:yield from nodes(c)
def write(p,m):
    if p.exists() or Path(str(p)+'.wat').exists():raise ValueError('Refuse overwrite')
    Path(str(p)+'.wat').write_text(wasm.emit(m),encoding='utf-8')
    wasm.tool('wat2wasm',[str(p)+'.wat','-o',p]);wasm.tool('wasm-validate',[p])
def signed(n):return (int(n)+2**31)%2**32-2**31
def canon(e):
    return sp.Poly(sp.expand(e),x,y).terms() if False else sp.expand(sum(signed(c)*x**a*y**b for (a,b),c in sp.Poly(sp.expand(e),x,y).terms()))
def expr(e):
    e=sp.sympify(e)
    if e==x:return ['local.get','0']
    if e==y:return ['local.get','1']
    if e.is_Integer:return ['i32.const',str(signed(e))]
    if e.is_Pow and e.exp.is_Integer and 0<=int(e.exp)<=16:
        return expr(sp.Mul(*([e.base]*int(e.exp)),evaluate=False)) if e.exp!=0 else expr(1)
    if e.is_Add or e.is_Mul:
        args=list(e.args)
        if not args:return expr(0 if e.is_Add else 1)
        result=expr(args[0])
        for a in args[1:]:result=['i32.add' if e.is_Add else 'i32.mul',result,expr(a)]
        return result
    raise ValueError('not an integer polynomial: '+str(e))
def module(a,b,quotient=False):
    init=''
    final='(i32.add (i32.add (local.get 0) (local.get 1)) (i32.mul (i32.const 7) (i32.mul (local.get 0) (local.get 1))))'
    if quotient:
        init='(local.set 3 (i32.add (local.get 0) (local.get 1))) (local.set 1 (i32.mul (local.get 0) (local.get 1))) (local.set 0 (local.get 3))'
        final='(i32.add (local.get 0) (i32.mul (i32.const 7) (local.get 1)))'
    return wasm.parse(f'''(module
      (func (param i32 i32) (result i32 i32) {wasm.emit(expr(a))} {wasm.emit(expr(b))})
      (func (export "run") (param i32 i32 i32) (result i32) (local i32)
        {init} (local.set 2 (i32.and (local.get 2) (i32.const 63)))
        (block (loop
          (br_if 1 (i32.eqz (local.get 2)))
          (call 0 (local.get 0) (local.get 1)) (local.set 1) (local.set 0)
          (local.set 2 (i32.sub (local.get 2) (i32.const 1))) (br 0))) {final}))''')

def polynomial(n,env):
    if not isinstance(n,list):raise ValueError('unexpected atom')
    k=n[0]
    if k=='i32.const':return sp.Integer(int(n[1]))
    if k=='local.get':return env[int(n[1])]
    if k=='local.tee':
        value=polynomial(n[2],env);env[int(n[1])]=value;return value
    if k in ('i32.add','i32.sub','i32.mul'):
        a=polynomial(n[1],env);b=polynomial(n[2],env)
        return {'i32.add':lambda:a+b,'i32.sub':lambda:a-b,'i32.mul':lambda:a*b}[k]()
    if k=='i32.shl' and n[2][0]=='i32.const':return polynomial(n[1],env)*2**(int(n[2][1])&31)
    raise ValueError('unsupported polynomial node '+k)

def step_values(f):
    params=[t for n in items(f,'param') for t in n[1:]]
    results=[t for n in items(f,'result') for t in n[1:]]
    if params!=['i32','i32'] or results!=['i32','i32']:raise ValueError('step signature')
    env={0:x,1:y};env.update({i+2:sp.Integer(0) for i,t in enumerate([t for n in items(f,'local') for t in n[1:]])})
    stack=[]
    for n in body(f):
        if n[0]=='local.set':env[int(n[1])]=polynomial(n[2],env)
        else:stack.append(polynomial(n,env))
    if len(stack)!=2:raise ValueError('step result count')
    return tuple(map(canon,stack))

def quotient(e):
    q,r,m=sp.symmetrize(sp.expand(e),x,y,formal=True)
    if r!=0:raise ValueError('non-symmetric expression')
    return sp.expand(q.subs({m[0][0]:x,m[1][0]:y}))

def encode(src,out):
    m=read(src);fs=items(m,'func')
    if any(n[0] not in ('type','func','export') for n in m[1:] if isinstance(n,list)):raise ValueError('module features')
    if len(fs)!=2 or items(m,'export')!=[['export','"run"',['func','1']]]:raise ValueError('private step, only run export required')
    a,b=step_values(fs[0])
    if sp.expand(a.xreplace({x:y,y:x})-b)!=0:raise ValueError('step not swap-equivariant')
    # Roundtrip canonical driver without writing any file.
    expected=items(module(a,b),'func')[1]
    expected=[n for n in body(expected) if not (isinstance(n,list) and n[0]=='export')]
    if body(fs[1])!=expected:raise ValueError('driver outside exact supported profile')
    A,B=quotient(a+b),quotient(a*b)
    assert sp.expand(A.subs({x:x+y,y:x*y},simultaneous=True)-a-b)==0
    assert sp.expand(B.subs({x:x+y,y:x*y},simultaneous=True)-a*b)==0
    write(out,module(A,B,True))
    return {'source':[str(a),str(b)],'quotient':[str(A),str(B)],'identity_over_Z':True,
            'inputSHA256':sha(src),'outputSHA256':sha(out)}

def extract(m):
    fs=items(m,'func');exports=items(m,'export')
    if len(exports)!=1 or exports[0][1]!='"run"':raise ValueError('export profile')
    run=fs[int(exports[0][2][1])]
    loops=[n for n in nodes(run) if n[0]=='loop']
    if len(loops)!=1:raise ValueError('one loop required')
    # Symbolically execute exactly one taken iteration, starting from arbitrary
    # current state. n=1 resolves the iteration guard, not any state branch.
    env={0:x,1:y,2:sp.Integer(1)}
    env.update({i+3:sp.Integer(0) for i in range(sum(len(n)-1 for n in items(run,'local')))})
    stack=[]
    def condition(n):
        if n[0]=='i32.eqz':v=polynomial(n[1],env);return 1 if v==0 else 0 if v.is_Integer else None
        v=polynomial(n,env);return bool(v) if v.is_Integer else None
    def walk(seq):
        for n in seq:
            if not isinstance(n,list):raise ValueError('unexpected loop atom')
            k=n[0]
            if k=='local.set':env[int(n[1])]=polynomial(n[2],env) if len(n)==3 else stack.pop()
            elif k=='call':
                a,b=step_values(fs[int(n[1])]);u=polynomial(n[2],env);v=polynomial(n[3],env)
                stack.extend([t.subs({x:u,y:v},simultaneous=True) for t in (a,b)])
            elif k=='br':return
            elif k=='br_if':
                c=condition(n[2])
                if c is None or c:raise ValueError('unexpected branch in taken iteration')
            elif k=='if':
                c=condition(n[1])
                if c is None:raise ValueError('state-dependent condition unsupported')
                arm=next((a for a in n[2:] if a[0]==('then' if c else 'else')),['then'])
                walk(arm[1:])
            elif k=='block':walk(n[1:])
            else:stack.append(polynomial(n,env))
    walk(loops[0][1:])
    if stack:raise ValueError('unexpected stack residue')
    return canon(env[0]),canon(env[1])

def attack(src,out):
    A,B=extract(read(src))
    Axy=A.subs({x:x+y,y:x*y},simultaneous=True);Bxy=B.subs({x:x+y,y:x*y},simultaneous=True)
    poly=sp.expand(z*z-Axy*z+Bxy)
    unit,factors=sp.factor_list(poly,z,x,y)
    roots=[]
    for factor,multiplicity in factors:
        f=sp.Poly(factor,z)
        if f.degree()!=1:raise ValueError('no linear factor over integer lift')
        root=-f.nth(0)/f.nth(1)
        if not sp.Poly(root,x,y).domain.is_ZZ:raise ValueError('noninteger lifted root')
        roots.extend([sp.expand(root)]*multiplicity)
    if len(roots)!=2 or canon(roots[0]+roots[1]-Axy)!=0 or canon(roots[0]*roots[1]-Bxy)!=0:raise ValueError('factor certificate failed')
    if canon(roots[0].xreplace({x:y,y:x})-roots[1])!=0:raise ValueError('not equivariant lift')
    write(out,module(*roots))
    return {'status':'recovered','roots':list(map(str,roots)),'quotient':[str(A),str(B)],
            'execution_queries':0,'inputSHA256':sha(src),'outputSHA256':sha(out),
            'scope':'recognized loop polynomial; output driver reconstructed for stated experimental profile'}

def build(out):
    out.mkdir();save(out/'plan.json',{'seed':20261018,'random_inputs':1024,'levels':['raw','O2','O3'],
      'task':'recover paired polynomial updates up to exchange, from binary alone',
      'kernels':['quadratic','cubic','coupled'],'assumption':'exact profile; pure i32; symmetric output x+y+7xy'})
    kernels={'quadratic':x*x+3*y+5,'cubic':x**3+2*x*y+y+7,'coupled':x*x*y+3*x+y*y+11}
    records=[];attacks=[];certificates=[]
    for name,a in kernels.items():
        d=out/name;d.mkdir();p=d/'plain.wasm';write(p,module(a,a.xreplace({x:y,y:x})))
        start=time.perf_counter();cert=encode(p,d/'quotient.wasm');elapsed=time.perf_counter()-start
        certificates.append({'kernel':name,'seconds':elapsed,**cert})
        for mode in ('plain','quotient'):
            for level in ('raw','O2','O3'):
                target=d/(mode+'-'+level+'.wasm')
                if level=='raw':target.write_bytes((d/(mode+'.wasm')).read_bytes())
                else:subprocess.run([str(wasm.TOOLS/'binaryen-version_133/bin/wasm-opt.exe'),str(d/(mode+'.wasm')),'-'+level,'--enable-multivalue','-o',str(target)],check=True,capture_output=True)
                wasm.tool('wasm-validate',[target]);Path(str(target)+'.wat').write_text(wasm.tool('wasm2wat',[target,'--fold-exprs']),encoding='utf-8')
                records.append({'kernel':name,'mode':mode,'level':level,'file':str(target.relative_to(out)),'bytes':target.stat().st_size,'sha256':sha(target)})
                if mode=='quotient':
                    start=time.perf_counter();r=d/('recovered-'+level+'.wasm')
                    try:
                        result=attack(target,r)
                        records.append({'kernel':name,'mode':'recovered','level':level,'file':str(r.relative_to(out)),'bytes':r.stat().st_size,'sha256':sha(r)})
                    except (ValueError,IndexError,KeyError) as e:result={'status':'unsupported','reason':str(e)}
                    attacks.append({'kernel':name,'level':level,'seconds':time.perf_counter()-start,**result})
    save(out/'manifest.json',{'artifacts':records,'attacks':attacks,'certificates':certificates,'python':sys.version,'sympy':sp.__version__,'sourceSHA256':sha(Path(__file__))})
    (out/'probe.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'artifacts':len(records),'attacks':attacks},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','encode','attack']);p.add_argument('source',type=Path);p.add_argument('output',type=Path,nargs='?');args=p.parse_args()
    if args.command=='build':build(args.source.resolve())
    else:print(json.dumps((encode if args.command=='encode' else attack)(args.source,args.output),indent=2))
