import json,random,statistics,subprocess,sys
from pathlib import Path
import prototype as p
q=p.q;src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
rows=[x for x in json.loads((src/'manifest.json').read_text()) if x['opt']=='O3' and x['kernel']!='zero-control' and x['mode'] in ('plain','eager','deferred','residual') and x['seed'] in (0,37)]
jobs=[]
for row in rows:
    target=out/row['file'];q.tool('wasm-opt',[src/row['file'],'-O3','-o',target])
    m=q.read(target);index=next(x[2][1] for x in m[1:] if x[:2]==['export','"run"'])
    def actual(k):
        normal=f'(i32.or (i32.and (i32.rotl (i32.xor (local.get 1) (local.get 3)) (i32.const {k*11})) (i32.const 8388607)) (i32.const {[0x3e800000,0xbf000000,0x3f000000][k]}))'
        zeros=f'(i32.shl (i32.and (i32.shr_u (local.get 3) (i32.const {k})) (i32.const 1)) (i32.const 31))'
        return f'(select {zeros} {normal} (local.get 2))'
    wrapper=f'''(module (func (param i32 i32 i32) (result i32) (local i32 i32)
      (block (loop (br_if 1 (i32.eq (local.get 3) (local.get 0)))
       (local.set 4 (i32.add (i32.add (i32.rotl (local.get 4) (i32.const 3))
        (call {index} {' '.join(actual(k) for k in range(3))})) (local.get 3)))
       (local.set 3 (i32.add (local.get 3) (i32.const 1))) (br 0))) (local.get 4)))'''
    idx=len([x for x in m[1:] if x[0]=='func']);m.append(q.w.parse(wrapper)[1]);m.append(['export','"bench"',['func',str(idx)]])
    dst=out/('bench-'+row['file']);q.compile(q.w.emit(m),dst)
    for distribution in ('normal','zero'):
        jobs.extend(dict(row,bench=dst.name,distribution=distribution,replicate=k) for k in range(5))
q.save(out/'manifest.json',rows)
for name in ('inputs.json','fixtures.json'):(out/name).write_bytes((src/name).read_bytes())
subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out),'--positive-only'],check=True,timeout=60)
random.Random(211026).shuffle(jobs);flags=['--no-liftoff','--no-wasm-lazy-compilation']
q.save(out/'protocol.json',dict(warmup=1024,batches=9,calibration_start=32,target_ns=10000000,maximum_batch=2**20,order_seed=211026,seed=37,kernels=['fma','horner12','rotation8'],flags=flags,jobs=jobs))
raw=[]
for j in jobs:
    baseline=out/f'bench-{j["kernel"]}-plain-0-O3.wasm'
    v=json.loads(subprocess.check_output(['node',*flags,str(Path(__file__).with_name('bench.cjs')),str(out/j['bench']),str(baseline),j['distribution']],text=True,timeout=60))
    raw.append(dict(j,**v));q.save(out/'runtime.json',raw)
    if len(raw)%20==0:print(json.dumps(dict(completed=len(raw),total=len(jobs))),flush=True)
summary=[]
for r in rows:
    for d in ('normal','zero'):
        g=[x for x in raw if x['file']==r['file'] and x['distribution']==d];med=[statistics.median(x['ns']) for x in g]
        summary.append(dict(kernel=r['kernel'],mode=r['mode'],distribution=d,median_ns=statistics.median(med),min_ns=min(med),max_ns=max(med),process_medians_ns=med,rss_kib_median=statistics.median(x['rss_kib'] for x in g),binary_bytes=(out/r['file']).stat().st_size,linear_memory_bytes=0,batch_counts=[x['batch'] for x in g]))
q.save(out/'summary.json',summary);print(json.dumps(dict(conditions=len(summary),processes=len(raw))))
