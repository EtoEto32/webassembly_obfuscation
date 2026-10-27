import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import prototype as p


def wrapper(core,n,steps):
    m=p.q.read(core);exports={e[1]:int(e[2][1]) for e in m[1:] if e[0]=='export'}
    run,reset=exports['"run"'],exports['"reset"'];mask=n-1
    body=f'''(func (export "bench") (param i32 i32) (result i32) (local i32 i32)
      (call {reset})
      (block $done (loop $L
        (br_if $done (i32.ge_u (local.get 2) (local.get 0)))
        (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
        (local.set 3 (i32.xor (local.get 3)
          (call {run} (i32.and (local.get 1) (i32.const {mask}))
            (i32.and (i32.shr_u (local.get 1) (i32.const 8)) (i32.const {mask}))
            (i32.and (i32.shr_u (local.get 1) (i32.const 16)) (i32.const {mask})) (i32.const {steps}))))
        (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br $L))) (local.get 3))'''
    return p.q.w.emit(m)[:-1]+body+')'


def main(main_dir,out):
    main_dir=Path(main_dir).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    variants=[]
    for n in (4,16,128):
        name='n%d-v0'%n
        for mode in ('plain','fixed','moving','recovered'):
            if mode=='recovered':
                raw=main_dir/(name+'-moving-O3-recovered.wasm');core=out/(name+'-recovered-O3.wasm')
                p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',core])
            else:core=main_dir/(name+'-'+mode+'-O3.wasm')
            for steps in (0,8,64):
                f=out/('%s-%s-s%d-bench.wasm'%(name,mode,steps));p.q.compile(wrapper(core,n,steps),f)
                variants.append(dict(n=n,mode=mode,steps=steps,file=f.name,core_bytes=core.stat().st_size,memory_bytes=65536))
    # Every wrapper must agree before timing; reset happens in bench itself.
    script='''const fs=require('fs');const files=JSON.parse(fs.readFileSync(process.argv[1]));let count=0;
      for(const n of [4,16,128])for(const s of [0,8,64])for(const k of [0,1,2,31,1024]){
        const vals=files.filter(x=>x.n===n&&x.steps===s).map(x=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(x.file))).exports.bench(k,0x41b3917));
        if(new Set(vals).size!==1)throw Error(JSON.stringify({n,s,k,vals}));count+=vals.length;}console.log(count);'''
    p.q.save(out/'wrapper-inputs.json',[dict(v,file=str(out/v['file'])) for v in variants])
    r=subprocess.run(['node','-e',script,str(out/'wrapper-inputs.json')],capture_output=True,text=True,timeout=60)
    if r.returncode:raise RuntimeError(r.stderr)
    p.q.save(out/'wrapper-check.json',dict(calls=int(r.stdout),mismatches=0))
    schedule=[(v,repeat) for v in variants for repeat in range(3)];random.Random(20261023).shuffle(schedule)
    raw=[]
    for v,repeat in schedule:
        r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.ROOT/'research/span-mask/bench.cjs'),str(out/v['file'])],capture_output=True,text=True,timeout=60)
        if r.returncode:raise RuntimeError(r.stderr)
        raw.append(dict(**v,repeat=repeat,measurement=json.loads(r.stdout)))
        p.q.save(out/'raw.json',raw)
        if len(raw)%12==0:print('processes',len(raw),flush=True)
    summary=[]
    for v in variants:
        procs=[x['measurement'] for x in raw if x['file']==v['file']]
        vals=[x for proc in procs for x in proc['ns_per_call']]
        summary.append(dict(**v,median_ns=statistics.median(vals),min_ns=min(vals),max_ns=max(vals),process_medians=[statistics.median(x['ns_per_call']) for x in procs],max_rss_kib=max(x['max_rss_kib'] for x in procs)))
    p.q.save(out/'summary.json',dict(rows=summary,processes=len(raw),batches=sum(len(x['measurement']['batches']) for x in raw),under_10ms=sum(b['ms']<10 for x in raw for b in x['measurement']['batches'])))


if __name__=='__main__':main(*sys.argv[1:])
