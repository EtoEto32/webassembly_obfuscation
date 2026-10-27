"""A deliberately restricted continuation split and target-only normalizer.

Accepts one exported pure i32 expression over parameter zero and constants.
The candidate is tested, not asserted novel. No memory, calls or traps.
"""
import importlib.util, pathlib, subprocess, time, json, random, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('sexpr',ROOT/'research/connectivity-elimination/prototype.py')
sx=importlib.util.module_from_spec(spec);spec.loader.exec_module(sx)
BIN=ROOT/'.tools/binaryen-version_133/bin'
OPS={'i32.add','i32.sub','i32.mul','i32.xor','i32.and','i32.or'}
CALLS=[]
def tool(name,*args):
    p=subprocess.run([str(BIN/(name+'.exe')),*map(str,args)],capture_output=True,text=True,timeout=30)
    CALLS.append(dict(tool=name,args=list(map(str,args)),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
    if p.returncode: raise RuntimeError(p.stdout+p.stderr)
    return p.stdout
def read(path):
    return sx.parse(tool('wasm-dis',path))
def nodes(t,op):
    if not isinstance(t,list):return []
    return ([t] if t and t[0]==op else [])+sum((nodes(v,op) for v in t[1:]),[])
def replace(t,old,new):
    if t==old:return new
    return [replace(v,old,new) for v in t] if isinstance(t,list) else t
def exprmod(e):
    return '(module (func (export "run") (param $x i32) (result i32) '+sx.emit(e)+'))'
def compile(wat,path):
    path.with_suffix('.wat').write_text(wat,encoding='utf-8')
    tool('wasm-as',path.with_suffix('.wat'),'--all-features','-o',path)
def chain(e,param):
    out=[]
    while isinstance(e,list) and e[0] in OPS:
        if len(e)!=3 or e[2][0]!='i32.const':raise ValueError('constant-right chain only')
        out.append((e[0],e[2]));e=e[1]
    if e!=['local.get',param]:raise ValueError('one immutable parameter only')
    return out[::-1]
def apply(ops,e):
    for op,k in ops:e=[op,e,k]
    return e
def transform(src,dst,a,b):
    m=read(src)
    if any(t[0] not in ('type','export','func') for t in m[1:]):raise ValueError('unsupported module feature')
    fs=nodes(m,'func')
    fs=[f for f in fs if len(f)>2 and isinstance(f[1],str)]
    if len(fs)!=1:raise ValueError('one function required')
    f=fs[0]; ps=nodes(f,'param')
    if len(ps)!=1 or ps[0][2:]!=['i32'] or nodes(f,'local'):raise ValueError('one i32 param, no locals')
    if nodes(f,'result')!=[['result','i32']]:raise ValueError('i32 result required')
    ops=chain(f[-1],ps[0][1])
    if not 0<a<b<len(ops):raise ValueError('three nonempty segments required')
    pre=apply(ops[:a],['local.get','$x'])
    work=apply(ops[b:],['suspend','$t',pre])
    mid=apply(ops[a:b],['local.get','$v'])
    wat='''(module
      (type $ft (func (param i32) (result i32))) (type $ct (cont $ft))
      (tag $t (param i32) (result i32))
      (func $worker (param $x i32) (result i32) WORK)
      (elem declare func $worker)
      (func (export "run") (param $x i32) (result i32)
        (local $k (ref null $ct)) (local $v i32)
        (block $on (result i32 (ref $ct))
          (return (resume $ct (on $t $on) (local.get $x) (cont.new $ct (ref.func $worker)))))
        (local.set $k) (local.set $v)
        (resume $ct MID (local.get $k))))'''.replace('WORK',sx.emit(work)).replace('MID',sx.emit(mid))
    compile(wat,dst)
def recover(src,dst):
    # Read only target binary, never source, cuts, random seed or expected expression.
    m=read(src);fs=[f for f in m[1:] if f[0]=='func']
    workers=[f for f in fs if nodes(f,'suspend')]
    if len(workers)!=1 or len(fs)!=2:raise ValueError('outside restricted split profile')
    w=workers[0];d=next(f for f in fs if f!=w)
    ss=nodes(w,'suspend');rs=nodes(d,'resume')
    if len(ss)!=1 or len(rs)!=2:raise ValueError('expected one suspension and two resumes')
    final=next(r for r in rs if not any(isinstance(c,list) and c and c[0]=='on' for c in r[2:]))
    # Binaryen retains the popped suspension payload as a named local.get.
    mid=final[2]
    pre=ss[0][2]
    gets=nodes(mid,'local.get')
    if nodes(mid,'resume'):
        # O3 sinks the handler-producing block into the payload expression.
        # Match only the observed Binaryen tuple-unpacking template.
        leaf=mid
        while isinstance(leaf,list) and leaf[0] in OPS and leaf[2][0]=='i32.const':leaf=leaf[1]
        if leaf[0]!='local.tee' or len(nodes(leaf,'resume'))!=1 or len(nodes(leaf,'tuple.extract'))!=2:
            raise ValueError('unsupported optimized payload extraction')
        middle=replace(mid,leaf,pre)
    else:
        if len(gets)!=1:raise ValueError('one payload input required')
        middle=replace(mid,gets[0],pre)
    e=replace(w[-1],ss[0],middle)
    param=nodes(w,'param')[0][1]
    e=replace(e,['local.get',param],['local.get','$x'])
    chain(e,'$x')
    compile(exprmod(e),dst)
    return e
def value(ops,x):
    for op,k in ops:
        k=int(k[1]);x={'i32.add':lambda:x+k,'i32.sub':lambda:x-k,'i32.mul':lambda:x*k,'i32.xor':lambda:x^k,'i32.and':lambda:x&k,'i32.or':lambda:x|k}[op]()&0xffffffff
    return x if x<0x80000000 else x-0x100000000
def main():
    out=ROOT/sys.argv[1];out.mkdir(parents=True,exist_ok=False)
    rng=random.Random(20261021); rows=[]
    for n in (8,32,128):
      for seed in range(3):
        # Each operation is a permutation of i32: prevent accidental constant kernels.
        ops=[]
        for _ in range(n):
          op=rng.choice(['i32.add','i32.sub','i32.mul','i32.xor']);k=rng.randrange(-2147483648,2147483648)
          if op=='i32.mul':k|=1
          ops.append((op,['i32.const',str(k)]))
        e=apply(ops,['local.get','$x']);base=out/f'n{n}-s{seed}.wasm';compile(exprmod(e),base)
        for split in (1,2,3):
          a=max(1,n*split//5);b=min(n-1,a+max(1,n//5))
          dst=out/f'n{n}-s{seed}-cut{split}.wasm'
          t=time.perf_counter();transform(base,dst,a,b);tx=time.perf_counter()-t
          rec=dst.with_name(dst.stem+'-recovered.wasm')
          t=time.perf_counter();actual=recover(dst,rec);rx=time.perf_counter()-t
          assert actual==e
          xs=[0,1,-1,2147483647,-2147483648]+[rng.randrange(-2147483648,2147483648) for _ in range(100)]
          checks='\n'.join('(assert_return (invoke "run" (i32.const %d)) (i32.const %d))'%(x,value(ops,x)) for x in xs)
          for label,p in [('source',base),('target',dst),('recovered',rec)]:
            wast=dst.with_name(dst.stem+'-'+label+'.wast');wast.write_text(tool('wasm-dis',p)+'\n'+checks,encoding='utf-8')
            tool('wasm-shell',wast);wast.with_suffix('.log').write_text(CALLS[-1]['stdout']+CALLS[-1]['stderr'],encoding='utf-8')
          rows.append(dict(n=n,seed=seed,cut=[a,b],inputs=len(xs),exact_expression=True,source_bytes=base.stat().st_size,target_bytes=dst.stat().st_size,transform_seconds=tx,recovery_including_tools_seconds=rx))
    (out/'records.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (out/'commands.json').write_text(json.dumps(CALLS,indent=2),encoding='utf-8')
    print(json.dumps(dict(conditions=len(rows),calls=sum(r['inputs']*3 for r in rows),all_exact=True)))
if __name__=='__main__':main()
