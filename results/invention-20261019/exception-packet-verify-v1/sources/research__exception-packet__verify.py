import argparse,json,re,subprocess,statistics,time,sys
from pathlib import Path
import prototype as p
import recover as r
from run import save,snapshot
sys.path.insert(0,str(p.ROOT/'.tools/encoding-synthesis-python'))
import z3
def oracle(kernel,k,x,y,z):
    mask=0xffffffff;h=x&mask
    def rot(v,n):return ((v<<n)|(v>>(32-n)))&mask
    for j in range(k):
        c=z&(1 if j%2==0 else 0x80000000)
        if kernel=='blend':h^=rot((x+j*123+17)&mask,j%31+1) if c else ((y^(j*311+91))*(j*2+3))&mask
        else:
            if kernel=='rolling':c=(x>>(j%8))&1
            h=(h+(j+1)*12345)&mask if c else rot((h^y)&mask,j%31+1)
    return h&mask
def model(t,variables):
    memo={}
    def f(x):
        if x in memo:return memo[x]
        op=x[0]
        if op=='arg':v=variables[x[1]]
        elif op=='i32.const':v=z3.BitVecVal(x[1],32)
        else:
            a=[f(y) for y in x[1:]]
            binary={'i32.add':lambda:a[0]+a[1],'i32.sub':lambda:a[0]-a[1],'i32.mul':lambda:a[0]*a[1],'i32.and':lambda:a[0]&a[1],'i32.or':lambda:a[0]|a[1],'i32.xor':lambda:a[0]^a[1],
              'i32.shl':lambda:a[0]<<(a[1]&31),'i32.shr_u':lambda:z3.LShR(a[0],a[1]&31),'i32.shr_s':lambda:a[0]>>(a[1]&31),'i32.rotl':lambda:z3.RotateLeft(a[0],a[1]),'i32.rotr':lambda:z3.RotateRight(a[0],a[1])}
            if op in binary:v=binary[op]()
            elif op=='select':v=z3.If(a[2]!=0,a[0],a[1])
            elif op=='i32.eqz':v=z3.If(a[0]==0,z3.BitVecVal(1,32),z3.BitVecVal(0,32))
            else:
                cond={'i32.eq':lambda:a[0]==a[1],'i32.ne':lambda:a[0]!=a[1],'i32.lt_s':lambda:a[0]<a[1],'i32.lt_u':lambda:z3.ULT(a[0],a[1]),'i32.gt_s':lambda:a[0]>a[1],'i32.gt_u':lambda:z3.UGT(a[0],a[1]),'i32.le_s':lambda:a[0]<=a[1],'i32.le_u':lambda:z3.ULE(a[0],a[1]),'i32.ge_s':lambda:a[0]>=a[1],'i32.ge_u':lambda:z3.UGE(a[0],a[1])}
                if op not in cond:raise ValueError('SMT op '+op)
                v=z3.If(cond[op](),z3.BitVecVal(1,32),z3.BitVecVal(0,32))
        memo[x]=v;return v
    return f(t)
def main(src,out):
    src=Path(src);out=Path(out);out.mkdir(parents=True,exist_ok=False);snapshot(out)
    m=json.loads((src/'manifest.json').read_text());cases=[(0,0,0),(1,2,1),(0x7fffffff,0x80000000,0x80000000),(0xffffffff,0x55555555,0xffffffff)]
    interpreter=[];proofs=[];timings=[];variables=z3.BitVecs('x y z',32)
    for row in m['files']:
        tree=p.binaryen_tree(src/row['file']);fn=next(x[2][1] for x in tree[1:] if x[0]=='export')
        for i,args in enumerate(cases):tree.append(['func',['export',f'"check{i}"'],['result','i32'],['call',fn,*[['i32.const',str(v)] for v in args]]])
        wrapped=out/row['file'];p.compile(p.w.emit(tree),wrapped)
        log=p.w.tool('wasm-interp',[wrapped,'--enable-all','--run-all-exports']);wrapped.with_suffix('.log').write_text(log,encoding='utf-8')
        values=[int(x) for x in re.findall(r'check\d+\(\) => i32:(\d+)',log)]
        expected=[oracle(row['kernel'],row['k'],*args) for args in cases]
        if values!=expected:raise AssertionError((row,values,expected,log))
        interpreter.append(dict(file=row['file'],calls=len(cases),values=values))
        source=src/f"{row['kernel']}{row['k']}-source.wasm";rec=src/row['recovered']
        lhs=model(p.read(source)[2],variables);rhs=model(p.read(rec)[2],variables);solver=z3.Solver();solver.set(timeout=10000);solver.add(lhs!=rhs)
        tick=time.perf_counter();status=str(solver.check());elapsed=(time.perf_counter()-tick)*1000
        proofs.append(dict(file=row['file'],status=status,ms=elapsed));save(out/'scalar-model-equivalence.json',dict(z3=z3.get_version_string(),proofs=proofs))
        # Reconstruct a fresh semantic model each time, with no global intern pool.
        clean=p.binaryen_tree(src/row['file']);times=[]
        for i in range(10):
            p.POOL.clear();tick=time.perf_counter();engine=r.Recover(clean);engine.run();t=(time.perf_counter()-tick)*1000
            if i:times.append(t)
        timings.append(dict(file=row['file'],median_ms=statistics.median(times),samples_ms=times,steps=engine.steps,max_flows=engine.max_flows))
    save(out/'interpreter.json',dict(status='passed',calls=sum(x['calls'] for x in interpreter),records=interpreter))
    save(out/'analysis-fresh-pool.json',timings)
    # 3 different alias/condition lifetimes, deliberately outside benchmark pattern.
    extra=[]
    bodies={
      'mutable-param':'(local.set $h (select (local.get 0) (local.get 1) (local.get 2))) (local.set 2 (i32.xor (local.get 2) (i32.const 1))) (i32.add (local.get $h) (select (local.get 0) (local.get 1) (local.get 2)))',
      'unmasked':'(i32.xor (select (local.get 0) (local.get 1) (local.get 2)) (select (i32.add (local.get 0) (i32.const 7)) (i32.sub (local.get 1) (i32.const 3)) (local.get 2)))',
      'derived':'(local.set $h (select (local.get 0) (local.get 1) (local.get 2))) (select (i32.add (local.get $h) (i32.const 7)) (local.get 1) (local.get $h))'}
    for name,body in bodies.items():
        source=out/(name+'-source.wasm');p.compile('(module (func (export "run") (param i32 i32 i32) (result i32) (local $h i32) '+body+'))',source)
        for mode in ('fresh','shared'):
            raw=out/f'{name}-{mode}-raw.wasm';info=p.transform(source,raw,mode)
            for opt in ('raw','O3'):
                target=raw if opt=='raw' else out/f'{name}-{mode}-O3.wasm'
                if opt=='O3':p.optimize(raw,target)
                rec=out/(target.stem+'-recovered.wasm');attack=r.recover(target,rec)
                extra.append(dict(source=source.name,file=target.name,recovered=rec.name,captures=info['captures'],attack=attack))
    save(out/'extra-manifest.json',extra)
    # Concrete wrong transform and null packet; validate first.
    n,name,e=p.read(src/'blend4-source.wasm');text,_=p.wat(n,name,e,'shared')
    wrong=out/'wrong-handler.wasm';p.compile(text.replace('(call $force1','(call $force0'),wrong)
    tree=p.w.parse(text)
    def nullify(x):
        if not isinstance(x,list):return x
        if x[:2]==['call','$capture']:return ['ref.null','exn']
        return [nullify(v) for v in x]
    null=out/'null-packet.wasm';p.compile(p.w.emit(nullify(tree)),null)
    refused=[]
    for name,wat in {
     'memory':'(module (memory 1) (func (export "run") (param i32) (result i32) (local.get 0)))',
     'division':'(module (func (export "run") (param i32) (result i32) (i32.div_u (i32.const 7) (local.get 0))))',
     'loop':'(module (func (export "run") (param i32) (result i32) (loop (result i32) (local.get 0))))',
     'import':'(module (import "x" "f" (func $f (param i32) (result i32))) (export "run" (func $f)))'}.items():
        file=out/(name+'-refuse.wasm');p.compile(wat,file)
        try:p.transform(file,out/(name+'-bad-accepted.wasm'),'shared');raise AssertionError('Accepted '+name)
        except ValueError as ex:refused.append(dict(name=name,reason=str(ex)))
    save(out/'refusals.json',refused)
    code=r'''const fs=require('fs'),path=require('path');const dir=process.argv[1],src=process.argv[2];
const load=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports.run;
const m=JSON.parse(fs.readFileSync(path.join(dir,'extra-manifest.json')));let seed=123456789;function rnd(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed|0;}
const xs=[[0,0,0],[1,2,0],[1,2,1],[-1,0,-2147483648],[13,17,2],[13,17,-1]];for(let i=0;i<512;i++)xs.push([rnd(),rnd(),rnd()]);let calls=0,errors=0;
for(const r of m){const base=load(path.join(dir,r.source));for(const field of ['file','recovered']){const f=load(path.join(dir,r[field]));for(const x of xs){const a=base(...x),b=f(...x);calls+=2;if(a!==b)errors++;}}}
const base=load(path.join(src,'blend4-source.wasm'));const wrong=load(path.join(dir,'wrong-handler.wasm')),nil=load(path.join(dir,'null-packet.wasm'));let wrongDiff=0,nullTraps=0;for(const x of xs){if(wrong(...x)!==base(...x))wrongDiff++;try{nil(...x);}catch(e){if(e instanceof WebAssembly.RuntimeError)nullTraps++;else throw e;}}
if(errors||!wrongDiff||nullTraps!==xs.length)throw Error('Verification failed');console.log(JSON.stringify({calls,errors,inputs:xs.length,wrong_handler_mismatches:wrongDiff,null_packet_traps:nullTraps}));'''
    proc=subprocess.run(['node','-e',code,str(out),str(src)],check=True,capture_output=True,text=True,timeout=60);checks=json.loads(proc.stdout);save(out/'extra-correctness.json',checks)
    # The attack must reject an actual nullable packet reaching throw_ref.
    try:r.recover(null,out/'null-recovered.wasm');raise AssertionError('Null accepted')
    except ValueError as ex:save(out/'null-attack-refusal.json',dict(reason=str(ex)))
    save(out/'summary.json',dict(status='completed',interpreter_calls=len(interpreter)*4,scalar_models=len(proofs),unsat=sum(x['status']=='unsat' for x in proofs),extra=checks,refusals=len(refused)))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('input');a.add_argument('output');v=a.parse_args();main(v.input,v.output)
