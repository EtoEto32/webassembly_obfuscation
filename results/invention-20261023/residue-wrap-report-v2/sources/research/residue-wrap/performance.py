import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import prototype as p


def wrapper(core):
    m=p.q.read(core)
    run=next(int(e[2][1]) for e in m[1:] if e[0]=='export' and e[1]=='"run"')
    body=f'''(func (export "bench") (param i32 i32) (result i32) (local i32 i32 i32)
      (block $done (loop $L
        (br_if $done (i32.ge_u (local.get 2) (local.get 0)))
        (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
        (local.set 4 (i32.add (i32.mul (local.get 1) (i32.const 1103515245)) (i32.const 12345)))
        (local.set 3 (i32.xor (local.get 3) (call {run} (local.get 1) (local.get 4))))
        (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br $L))) (local.get 3))'''
    return p.q.w.emit(m)[:-1]+body+')'


def main(main_dir,dest):
    main_dir=Path(main_dir).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False);variants=[]
    for name in ('add','multiply','polynomial'):
        for mode in ('plain','repair','aligned','recovered'):
            if mode=='recovered':
                core=out/(name+'-recovered-O3.wasm');p.q.w.tool('wasm-opt',[main_dir/(name+'-aligned-O3-recovered.wasm'),'-O3','-o',core])
            else:core=main_dir/(name+'-'+mode+'-O3.wasm')
            f=out/(name+'-'+mode+'-bench.wasm');p.q.compile(wrapper(core),f)
            variants.append(dict(name=name,mode=mode,file=f.name,core_bytes=core.stat().st_size,linear_memory_bytes=0))
    p.q.save(out/'inputs.json',[dict(v,file=str(out/v['file'])) for v in variants])
    script='''const fs=require('fs');const files=JSON.parse(fs.readFileSync(process.argv[1]));let calls=0;
      for(const name of ['add','multiply','polynomial'])for(const n of [0,1,31,1024])for(const seed of [0,1,0x41b3917]){
        const values=files.filter(x=>x.name===name).map(x=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(x.file))).exports.bench(n,seed));
        if(new Set(values).size!==1)throw Error(JSON.stringify({name,n,seed,values}));calls+=values.length;}console.log(calls);'''
    check=subprocess.run(['node','-e',script,str(out/'inputs.json')],capture_output=True,text=True,timeout=60)
    if check.returncode:raise RuntimeError(check.stderr)
    p.q.save(out/'wrapper-check.json',dict(calls=int(check.stdout),mismatches=0))
    schedule=[(v,i) for v in variants for i in range(3)];random.Random(20261023).shuffle(schedule);raw=[]
    for v,i in schedule:
        proc=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.ROOT/'research/span-mask/bench.cjs'),str(out/v['file'])],capture_output=True,text=True,timeout=60)
        if proc.returncode:raise RuntimeError(proc.stderr)
        raw.append(dict(**v,repeat=i,measurement=json.loads(proc.stdout)));p.q.save(out/'raw.json',raw)
        if len(raw)%12==0:print('processes',len(raw),flush=True)
    rows=[]
    for v in variants:
        procs=[x['measurement'] for x in raw if x['file']==v['file']];vals=[x for proc in procs for x in proc['ns_per_call']]
        rows.append(dict(**v,median_ns=statistics.median(vals),min_ns=min(vals),max_ns=max(vals),process_medians=[statistics.median(proc['ns_per_call']) for proc in procs],max_rss_kib=max(proc['max_rss_kib'] for proc in procs)))
    summary=dict(rows=rows,processes=len(raw),batches=sum(len(x['measurement']['batches']) for x in raw),under_10ms=sum(b['ms']<10 for x in raw for b in x['measurement']['batches']))
    p.q.save(out/'summary.json',summary);print(json.dumps(summary))


if __name__=='__main__':main(*sys.argv[1:])
