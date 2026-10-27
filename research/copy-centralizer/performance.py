import json,random,statistics,subprocess,sys
from pathlib import Path
import prototype as p
q=p.q;src,out=map(Path,sys.argv[1:3]);dispatch='--dispatch' in sys.argv[3:];out.mkdir(parents=True,exist_ok=False)
rows=[r for r in json.loads((src/'manifest.json').read_text()) if r['opt']=='O3'];manifest=[]
for r in rows:
    module=q.read(src/r['file']);exports={x[1][1:-1]:int(x[2][1]) for x in module[1:] if x[0]=='export' and x[2][0]=='func'};idx=len([x for x in module[1:] if x[0]=='func'])
    calls=' '.join(f'(call {exports["copy"+str(j)]})' for j in range(len(r['copies'])))
    if dispatch:
        calls=''
        for j in reversed(range(len(r['copies']))):
            call=f'(call {exports["copy"+str(j)]})'
            calls=call if not calls else f'(if (i32.eq (i32.rem_u (i32.shr_u (local.get 1) (i32.const 8)) (i32.const {len(r["copies"])})) (i32.const {j})) (then {call}) (else {calls}))'
    body=f'''(func (param i32) (result i32) (local i32 i32)
      (local.set 1 (i32.const 123)) (block (loop
      (br_if 1 (i32.eqz (local.get 0)))
      (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
      (call {exports['write']} (i32.and (local.get 1) (i32.const {r['n']-1})) (local.get 1))
      {calls}
      (local.set 2 (i32.xor (local.get 2) (call {exports['read']} (i32.and (i32.shr_u (local.get 1) (i32.const 4)) (i32.const {r['n']-1})))))
      (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0))) (local.get 2))'''
    module.append(q.w.parse('(module '+body+')')[1]);module.append(['export','"bench"',['func',str(idx)]])
    dst=out/r['file'];q.compile(q.w.emit(module),dst);manifest.append(dict(kernel=r['kernel'],mode=r['mode'],file=dst.name,sha256=q.digest(dst),core_sha256=r['sha256'],core_bytes=r['bytes']))
q.save(out/'manifest.json',manifest)
jobs=[dict(**r,repetition=i) for i in range(3) for r in manifest];random.Random(211045).shuffle(jobs)
q.save(out/'protocol.json',dict(warmup=128,batches=9,pilot_target_ns=5000000,max_iterations=1048576,order_seed=211045,flags=['--no-liftoff','--no-wasm-lazy-compilation'],copy_workload='one input-selected copy' if dispatch else 'all declared copies in order',unit='one logical byte write, copy workload, one logical byte read, loop and checksum',jobs=jobs))
results=[]
for job in jobs:
    value=json.loads(subprocess.check_output(['node','--no-liftoff','--no-wasm-lazy-compilation',str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])],text=True,timeout=60))
    results.append(dict(**job,**value));q.save(out/'runtime.json',results)
summary=[]
for r in manifest:
    rs=[v for v in results if v['file']==r['file']];medians=[statistics.median(v['ns']) for v in rs]
    summary.append(dict(**r,median_ns=statistics.median(medians),min_process_median_ns=min(medians),max_process_median_ns=max(medians),linear_memory_bytes=65536,rssBytes=[v['rssBytes'] for v in rs]))
# Every benchmark invocation starts its LCG afresh, but memory is persistent;
# checksum equality is checked only in a separate fresh-instance 257-iteration probe below.
probes=[]
for r in manifest:
    code='const fs=require("fs");const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;console.log(e.bench(257));'
    checksum=int(subprocess.check_output(['node','-e',code,str(out/r['file'])],text=True));probes.append(dict(kernel=r['kernel'],mode=r['mode'],checksum=checksum))
for k in {r['kernel'] for r in manifest}:assert len({v['checksum'] for v in probes if v['kernel']==k})==1
q.save(out/'checksums.json',probes);q.save(out/'summary.json',summary)
print(json.dumps(dict(processes=len(results),conditions=len(summary),summary=[{k:r[k] for k in ('kernel','mode','median_ns','core_bytes')} for r in summary])))
