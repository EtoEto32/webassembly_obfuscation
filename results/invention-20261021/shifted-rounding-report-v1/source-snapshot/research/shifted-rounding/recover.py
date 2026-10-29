"""Family-aware recovery of scaled rounding DAGs from the actual binary."""
import argparse
import hashlib
import json
import math
import time
from pathlib import Path
import prototype as p


def signature(f):
    # Normalize only spill/local choices in the pure, loop-free quantizer.
    # Branches and their return values remain explicit; this is not a generic
    # equivalence prover and does not ignore conditions or exceptional cases.
    params=p.base.decl(f,'param');env={i:['arg',str(i),t] for i,t in enumerate(params)}
    for i,t in enumerate(p.base.decl(f,'local'),len(params)):env[i]=[t+'.const','0']
    def value(e,env):
        if not isinstance(e,list):return e
        op=e[0]
        if op=='local.get':return env[int(e[1])]
        if op=='local.tee':
            x=value(e[2],env);env[int(e[1])]=x;return x
        if op.startswith(('i32.','i64.','f32.','f64.')):
            return [op,*[value(x,env) for x in e[1:]]]
        raise p.base.Unsupported('quantizer expression '+op)
    def code(xs,env):
        for j,e in enumerate(xs):
            if e[0]=='local.set':env[int(e[1])]=value(e[2],env)
            elif e[0]=='return':return value(e[1],env)
            elif e[0]=='if':
                condition=value(e[1],env)
                yes=next(x[1:] for x in e[2:] if x[0]=='then')
                no=next((x[1:] for x in e[2:] if x[0]=='else'),[])
                return ['ite',condition,code(yes+xs[j+1:],dict(env)),code(no+xs[j+1:],dict(env))]
            elif j==len(xs)-1:return value(e,env)
            else:raise p.base.Unsupported('quantizer statement '+e[0])
        raise p.base.Unsupported('quantizer without result')
    tree=['signature',['param',*params],['result',*p.base.decl(f,'result')],code(p.base.body(f),env)]
    return hashlib.sha256(p.q.w.emit(tree).encode()).hexdigest()


def prepare_profiles(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    raw=out/'quant-known-raw.wasm'
    p.q.compile('(module '+p.quantizer()+' (export "q" (func $quant)))',raw)
    opt=out/'quant-known-O3.wasm'
    p.q.tool('wasm-opt',[raw,'-O3','-o',opt])
    profiles=[]
    zero=out/'quant-zero-raw.wasm'
    zero_text=p.quantizer().replace('(param $p i32)','').replace('(local.get $p)','(i32.const 0)')
    p.q.compile('(module '+zero_text+' (export "q" (func $quant)))',zero)
    zero_opt=out/'quant-zero-O3.wasm'
    p.q.tool('wasm-opt',[zero,'-O3','-o',zero_opt])
    for file in (raw,opt,zero,zero_opt):
        fs=[e for e in p.q.read(file)[1:] if e[0]=='func']
        assert len(fs)==1
        profiles.append(signature(fs[0]))
    p.q.save(out/'profiles.json',profiles)
    return profiles


def recover(src,profiles,dst=None):
    start=time.perf_counter_ns();module=p.q.read(src);read_end=time.perf_counter_ns()
    need=p.base.demand
    need(all(e[0] in ('func','type','export') for e in module[1:]),'pure module')
    fs=[e for e in module[1:] if e[0]=='func']
    helpers={i for i,f in enumerate(fs) if p.base.decl(f,'param') in (['f64'],['f64','i32'])
             and p.base.decl(f,'result')==['f64'] and signature(f) in profiles}
    need(len(helpers)==1,'known quantizer body required')
    helper=next(iter(helpers));f=fs[0]
    fixed_zero=p.base.decl(fs[helper],'param')==['f64']
    inlined=p.base.decl(f,'result')==['i32']
    n=len(p.base.decl(f,'param'))
    need(p.base.decl(f,'param')==[('i32' if inlined else 'f32')]*n and 1<=n<=16,'kernel signature')
    need(len(fs)==(2 if inlined else 3),'function profile')
    need([e for e in module[1:] if e[0]=='export']==[['export','"run"',['func',str(0 if inlined else 1)]]],'one run export')
    if not inlined:
        ref=p.q.w.parse('(module '+p.base.wrapper(n)+')')[1]
        need(p.base.body(fs[1])==p.base.body(ref),'canonicalizing wrapper')
    nodes=[('input',i) for i in range(n)];cache={t:i for i,t in enumerate(nodes)}
    env={i:(i,0,True) for i in range(n)} if not inlined else {}
    def intern(t):
        if t not in cache:cache[t]=len(nodes);nodes.append(t)
        return cache[t]
    def power(e):
        if e[0]!='f64.const':return None
        v=float.fromhex(e[1]);mantissa,exp=math.frexp(v)
        need(mantissa==0.5 and -96<=exp-1<=96,'positive bounded power of two')
        return exp-1
    def expr(e):
        op=e[0]
        if op=='local.get':
            need(int(e[1]) in env,'unknown local');return env[int(e[1])]
        if op=='local.tee':
            v=expr(e[2]);env[int(e[1])]=v;return v
        if op=='f64.promote_f32':
            inner=e[1]
            if inlined:
                need(inner[0]=='f32.reinterpret_i32' and inner[1][0]=='local.get','bit input')
                i=int(inner[1][1]);need(0<=i<n,'input index');return i,0,True
            need(inner[0]=='local.get' and 0<=int(inner[1])<n,'f32 input')
            return int(inner[1]),0,True
        if op=='f64.mul':
            a,b=e[1:];pa,pb=power(a),power(b)
            if pa is not None or pb is not None:
                if pa is not None:a,b=b,a;pb=pa
                v,k,rounded=expr(a);return v,k+pb,rounded
            va,ka,ra=expr(a);vb,kb,rb=expr(b)
            need(ra and rb,'unrounded multiplication input')
            return ('mul',va,vb),ka+kb,False
        if op in ('f64.add','f64.sub'):
            a,ka,ra=expr(e[1]);b,kb,rb=expr(e[2]);need(ra and rb and ka==kb,'aligned rounded addition')
            return (op[4:],a,b),ka,False
        if op=='call':
            need(int(e[1])==helper and len(e)==(3 if fixed_zero else 4),'quantizer call')
            if not fixed_zero:need(e[3][0]=='i32.const','constant grid phase')
            v,k,rounded=expr(e[2]);phase=0 if fixed_zero else int(e[3][1])
            need(k==phase and -32<=phase<=32 and not rounded,'quantizer phase / operation boundary')
            return intern(v),phase,True
        if op=='f32.demote_f64':
            v,k,rounded=expr(e[1]);need(k==0 and rounded,'final unscaled rounded result');return v,0,True
        raise p.base.Unsupported('expression '+op)
    code=p.base.body(f)
    for e in code[:-1]:
        need(e[0]=='local.set','straight statements');env[int(e[1])]=expr(e[2])
    result=code[-1]
    if inlined:
        need(result[0]=='select' and result[1]==['i32.const','2143289344'] and result[2][0]=='i32.reinterpret_f32','canonical result select')
        actual=result[2][1];need(actual[0]=='local.tee','result temp')
        idx=actual[1];need(result[3]==['f32.ne',['local.get',idx],['local.get',idx]],'NaN condition')
        root,phase,rounded=expr(actual)
    else:root,phase,rounded=expr(result)
    need(phase==0 and rounded,'final result')
    end=time.perf_counter_ns()
    if dst is not None:p.q.compile(p.generate(n,nodes,root,'plain',0)[0],dst)
    return dict(nodes=nodes,root=root,arguments=n,read_ms=(read_end-start)/1e6,
                recovery_ms=(end-read_end)/1e6,helper_index=helper)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('src');ap.add_argument('dst');ap.add_argument('--profiles',required=True)
    a=ap.parse_args();r=recover(a.src,json.loads(Path(a.profiles).read_text()),a.dst)
    print(json.dumps(r))
