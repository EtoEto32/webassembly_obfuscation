"""Shared Wasm loop, normal/zero inputs, three independent processes per cell."""
import json
import random
import statistics
import subprocess
import sys
from pathlib import Path
import prototype as p

main,out=map(lambda x:Path(x).resolve(),sys.argv[1:3]);out.mkdir(parents=True,exist_ok=False)
underflow='--underflow' in sys.argv[3:]
rows=[x for x in json.loads((main/'manifest.json').read_text()) if x['opt']=='O3' and x['kernel']!='cancellation']
jobs=[]
for row in rows:
    m=p.q.read(main/row['file']);idx=next(e[2][1] for e in m[1:] if e[:2]==['export','"run"'])
    def actual(k):
        if underflow:
            varying='(i32.or (i32.and (i32.xor (local.get 1) (local.get 3)) (i32.const 65535)) (i32.const 8388608))'
            patterns={'multiply-add':[varying,'(i32.const 1056964608)','(i32.const 0)'],
                      'horner6':['(i32.const 1056964608)','(i32.const 0)',varying],
                      'butterfly4':[varying,'(i32.const 1)','(i32.const 1056964608)']}
            return patterns[row['kernel']][k]
        normal=f'(i32.or (i32.and (i32.rotl (i32.xor (local.get 1) (local.get 3)) (i32.const {k*11})) (i32.const 8388607)) (i32.const {[0x3e800000,0xbf000000,0x3f000000][k]}))'
        zero=f'(i32.shl (i32.and (i32.shr_u (local.get 3) (i32.const {k})) (i32.const 1)) (i32.const 31))'
        return f'(select {zero} {normal} (local.get 2))'
    fn=f'''(module (func (param i32 i32 i32) (result i32) (local i32 i32)
       (block (loop (br_if 1 (i32.eq (local.get 3) (local.get 0)))
         (local.set 4 (i32.add (i32.add (i32.rotl (local.get 4) (i32.const 3))
           (call {idx} {' '.join(actual(k) for k in range(3))})) (local.get 3)))
         (local.set 3 (i32.add (local.get 3) (i32.const 1))) (br 0))) (local.get 4)))'''
    number=len([x for x in m[1:] if x[0]=='func'])
    m.extend([p.q.w.parse(fn)[1],['export','"bench"',['func',str(number)]]])
    dst=out/('bench-'+row['file']);p.q.compile(p.q.w.emit(m),dst)
    jobs.extend(dict(row,bench=dst.name,distribution=d,replicate=r) for d in (('underflow',) if underflow else ('normal','zero')) for r in range(3))
random.Random(21102192).shuffle(jobs)
flags=['--no-liftoff','--no-wasm-lazy-compilation']
runner=p.ROOT/'research/zero-sign-transport/bench.cjs'
p.q.save(out/'protocol.json',dict(jobs=jobs,flags=flags,runner=str(runner.relative_to(p.ROOT)),
    runner_sha256=p.q.digest(runner),warmup=1024,batches=9,target_ms=10,max_calls=2**20,order_seed=21102192))
raw=[]
for job in jobs:
    baseline=out/('bench-'+job['kernel']+'-plain-O3.wasm')
    proc=subprocess.run(['node',*flags,str(runner),str(out/job['bench']),str(baseline),job['distribution']],
                        capture_output=True,text=True,timeout=60)
    proc.check_returncode();raw.append(dict(job,**json.loads(proc.stdout)))
    p.q.save(out/'runtime.json',raw)
    if len(raw)%12==0:print(json.dumps(dict(done=len(raw),total=len(jobs))),flush=True)
summary=[]
for row in rows:
    for d in (('underflow',) if underflow else ('normal','zero')):
        rs=[x for x in raw if x['file']==row['file'] and x['distribution']==d]
        med=[statistics.median(x['ns']) for x in rs]
        summary.append(dict(kernel=row['kernel'],mode=row['mode'],distribution=d,median_ns=statistics.median(med),
                            process_medians_ns=med,bytes=row['bytes'],peak_rss_kib=[r['rss_kib'] for r in rs],
                            batch_calls=[r['batch'] for r in rs],linear_memory_bytes=0))
p.q.save(out/'summary.json',summary)
print(json.dumps(dict(conditions=len(summary),processes=len(raw))),flush=True)
