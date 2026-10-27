"""Restricted f32 arithmetic DAG with an explicit canonical-NaN bit API."""
import argparse,importlib.util,json,random,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('zs_common',ROOT/'research/isotope-swizzle/prototype.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
class Unsupported(ValueError):pass
def demand(ok,why):
    if not ok:raise Unsupported(why)
def body(f):return [x for x in f[1:] if isinstance(x,list) and x[0] not in ('type','param','result','local','export')]
def decl(f,k):return [t for x in f[1:] if isinstance(x,list) and x[0]==k for t in x[1:]]
def wrapper(n):
    args=' '.join(f'(f32.reinterpret_i32 (local.get {i}))' for i in range(n))
    return f'''(func (export "run") (param {' '.join(['i32']*n)}) (result i32) (local f32)
      (local.set {n} (call 0 {args}))
      (select (i32.const 2143289344) (i32.reinterpret_f32 (local.get {n}))
       (f32.ne (local.get {n}) (local.get {n}))))'''
def wrap(kernel,n):return '(module '+kernel+' '+wrapper(n)+')'
def parse_source(module):
    demand(all(x[0] in ('type','func','export') for x in module[1:]),'pure closed module')
    fs=[x for x in module[1:] if x[0]=='func'];demand(len(fs)==2,'kernel and bit wrapper')
    f=fs[0];params=decl(f,'param');n=len(params)
    demand(1<=n<=16 and set(params)=={'f32'} and decl(f,'result')==['f32'],'f32 kernel signature')
    demand(all(x=='f32' for x in decl(f,'local')),'f32 source locals')
    # Compare the actual canonicalizing wrapper, after stripping only type annotation.
    ref=q.w.parse('(module '+wrapper(n)+')')[1]
    expected=body(ref);demand(body(fs[1])==expected,'explicit canonical-NaN bit wrapper required')
    demand(decl(fs[1],'param')==['i32']*n and decl(fs[1],'result')==['i32'] and decl(fs[1],'local')==['f32'],'wrapper signature')
    demand([x for x in module[1:] if x[0]=='export']==[['export','"run"',['func','1']]],'only run export')
    nodes=[];cache={};env={};
    def intern(t):
        if t not in cache:cache[t]=len(nodes);nodes.append(t)
        return cache[t]
    for i in range(n):env[i]=intern(('input',i))
    # Default f32 locals are +0; exclude implicit reads instead of inventing source nodes.
    def expr(e):
        op=e[0]
        if op=='local.get':demand(int(e[1]) in env,'uninitialized local profile');return env[int(e[1])]
        if op=='local.tee':v=expr(e[2]);env[int(e[1])]=v;return v
        if op in ('f32.add','f32.sub','f32.mul'):return intern((op[4:],expr(e[1]),expr(e[2])))
        raise Unsupported('source operation '+op)
    code=body(f);demand(code,'nonempty kernel')
    for e in code[:-1]:demand(e[0]=='local.set','source statement');env[int(e[1])]=expr(e[2])
    root=expr(code[-1]);demand(nodes[root][0]!='input','arithmetic root')
    reachable=set()
    def visit(i):
        if i in reachable:return
        reachable.add(i)
        if nodes[i][0]!='input':visit(nodes[i][1]);visit(nodes[i][2])
    visit(root)
    # Retain source arguments even if unused, and prune dead computation.
    used=[i for i,t in enumerate(nodes) if i in reachable or t[0]=='input'];mapping={old:new for new,old in enumerate(used)}
    nodes=[t if t[0]=='input' else (t[0],mapping[t[1]],mapping[t[2]]) for i,t in enumerate(nodes) if i in mapping]
    demand(len(nodes)<=512,'node cap');return n,nodes,mapping[root]

def generate(n,nodes,root,mode='deferred',seed=37):
    demand(mode in ('plain','eager','deferred','uncorrected'),'mode')
    rng=random.Random(seed);ph=[rng.randrange(2) for _ in nodes] if mode!='plain' else [0]*len(nodes)
    k=len(nodes);v=lambda i:f'(local.get {n+i})';sg=lambda i:f'(local.get {n+k+i})'
    zero=lambda a:f'(f32.eq {a} (f32.const 0))'
    neg=lambda a,p:f'(f32.neg {a})' if p else a
    bit=lambda a:f'(i32.shr_u (i32.reinterpret_f32 {a}) (i32.const 31))'
    xor=lambda a,b:f'(i32.xor {a} {b})'
    band=lambda a,b:f'(i32.and {a} {b})'
    logicalbit=lambda i:xor(bit(v(i)),f'(i32.const {ph[i]})') if ph[i] else bit(v(i))
    code=[];shadow=[]
    for i,t in enumerate(nodes):
        if t[0]=='input':value=neg(f'(local.get {t[1]})',ph[i]);sign=bit(f'(local.get {t[1]})')
        else:
            op,a,b=t
            if mode=='plain':value=f'(f32.{op} {v(a)} {v(b)})'
            elif op=='mul':value=f'(f32.mul {neg(v(a),ph[a]^ph[b]^ph[i])} {v(b)})'
            else:value=f'(f32.add {neg(v(a),ph[a]^ph[i])} {neg(v(b),ph[b]^ph[i]^int(op=="sub"))})'
            sa,sb=sg(a),sg(b)
            if op=='mul':zs=xor(sa,sb)
            else:
                if op=='sub':sb=xor(sb,'(i32.const 1)')
                zs=band(band(zero(v(a)),zero(v(b))),band(sa,sb))
            sign=f'(select {zs} {logicalbit(i)} {zero(v(i))})'
        code.append(f'(local.set {n+i} {value})')
        if mode=='eager' and t[0] in ('add','sub'):
            op,a,b=t;sb=logicalbit(b)
            if op=='sub':sb=xor(sb,'(i32.const 1)')
            zs=band(band(zero(v(a)),zero(v(b))),band(logicalbit(a),sb))
            desired=xor(zs,f'(i32.const {ph[i]})') if ph[i] else zs
            repaired=f'(f32.reinterpret_i32 (i32.shl {desired} (i32.const 31)))'
            code.append(f'(local.set {n+i} (select {repaired} {v(i)} {zero(v(i))}))')
        shadow.append(f'(local.set {n+k+i} {sign})')
    result=neg(v(root),ph[root]);locals_=['f32']*k
    if mode=='deferred':
        locals_+=['i32']*k
        result=f'(if (result f32) {zero(v(root))} (then {"".join(shadow)} (f32.reinterpret_i32 (i32.shl {sg(root)} (i32.const 31)))) (else {result}))'
    kernel=f'(func (param {" ".join(["f32"]*n)}) (result f32) (local {" ".join(locals_)}) {"".join(code)} {result})'
    return wrap(kernel,n),dict(nodes=k,arithmetic_nodes=sum(t[0]!='input' for t in nodes),phases=ph,mode=mode)

def transform(src,dst,mode,seed):
    t=time.perf_counter();n,nodes,root=parse_source(q.read(src));text,info=generate(n,nodes,root,mode,seed);q.compile(text,dst)
    return dict(source_sha256=q.digest(src),output_sha256=q.digest(dst),seed=seed,elapsed_ms=(time.perf_counter()-t)*1000,**info)

def recover(src,dst):
    """Known-generating-family assumption; correction authenticity is not certified."""
    start=time.perf_counter();m=q.read(src);reader_ms=(time.perf_counter()-start)*1000;start=time.perf_counter()
    demand(all(x[0] in ('type','func','export') for x in m[1:]),'closed module')
    fs=[x for x in m[1:] if x[0]=='func'];demand(len(fs) in (1,2),'one inlined function or kernel/wrapper');f=fs[0];inlined=len(fs)==1
    n=len(decl(f,'param'));demand(decl(f,'param')==['i32' if inlined else 'f32']*n,'parameters')
    nodes=[('input',i) for i in range(n)];cache={t:i for i,t in enumerate(nodes)};env={} if inlined else {i:(i,0) for i in range(n)}
    def intern(t):
        if t not in cache:cache[t]=len(nodes);nodes.append(t)
        return cache[t]
    def expr(e):
        op=e[0]
        if op=='f32.reinterpret_i32':
            a=e[1];demand(inlined and a[0]=='local.get' and 0<=int(a[1])<n,'bit input');return int(a[1]),0
        if op=='local.get':demand(int(e[1]) in env,'nonfloat/unknown local');return env[int(e[1])]
        if op=='local.tee':v=expr(e[2]);env[int(e[1])]=v;return v
        if op=='f32.neg':v,p=expr(e[1]);return v,p^1
        if op in ('f32.add','f32.sub','f32.mul'):
            a,pa=expr(e[1]);b,pb=expr(e[2])
            if op=='f32.mul':return intern(('mul',a,b)),pa^pb
            return intern(('sub' if pa^pb^int(op=='f32.sub') else 'add',a,b)),pa
        if op=='if':
            branch=nonzero_branch(e);demand(branch,'nonzero result branch')
            for x in branch[:-1]:statement(x)
            return expr(branch[-1])
        raise Unsupported('float extraction '+op)
    def nonzero_branch(e):
        children=[x for x in e[1:] if isinstance(x,list) and x[0] not in ('result','then','else')]
        demand(len(children)==1 and children[0][0] in ('f32.eq','f32.ne'),'zero branch condition');cond=children[0]
        a,b=cond[1:];
        if a[0]=='f32.const':a,b=b,a
        demand(b[0]=='f32.const' and float.fromhex(b[1])==0,'zero comparator')
        expr(a)  # Preserve local.tee effects in the condition.
        tag='else' if cond[0]=='f32.eq' else 'then'
        return next((x[1:] for x in e if isinstance(x,list) and x[0]==tag),[])
    def statement(e):
        if e[0]=='local.set':env[int(e[1])]=expr(e[2]);return
        if e[0]=='if':
            for x in nonzero_branch(e):statement(x)
            return
        raise Unsupported('stage statement '+e[0])
    code=body(f)
    for e in code[:-1]:statement(e)
    final=code[-1]
    if inlined:
        demand(final[0]=='select' and final[1]==['i32.const','2143289344'],'canonical NaN select')
        demand(final[2][0]=='i32.reinterpret_f32','bit result');final=final[2][1]
    result,p=expr(final);demand(p==0,'decoded root phase')
    text,_=generate(n,nodes,result,'plain',0);analysis_ms=(time.perf_counter()-start)*1000
    q.compile(text,dst)
    return dict(reader_ms=reader_ms,analysis_ms=analysis_ms,nodes=len(nodes),arithmetic_nodes=len(nodes)-n,output_sha256=q.digest(dst),source_sha256=q.digest(src),assumption='genuine deferred output; shadow authenticity not independently certified')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['transform','recover']);p.add_argument('source');p.add_argument('output');p.add_argument('--mode',default='deferred');p.add_argument('--seed',type=int,default=37);a=p.parse_args()
    print(json.dumps(transform(a.source,a.output,a.mode,a.seed) if a.command=='transform' else recover(a.source,a.output)))
