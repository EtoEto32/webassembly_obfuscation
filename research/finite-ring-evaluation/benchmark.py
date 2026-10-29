import json,random,statistics,subprocess,sys
from pathlib import Path
from isolate import q
src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
rows=[x for x in json.loads((src/'manifest.json').read_text()) if x['opt']=='O3'];jobs=[]
for r in rows:
    m=q.read(src/r['file']);index=next(x[2][1] for x in m[1:] if x[:2]==['export','"run"'])
    wrapper=f'''(module (func (export "bench") (param i32 i32) (result i32) (local i32 i32)
      (block (loop (br_if 1 (i32.eq (local.get 2) (local.get 0)))
      (local.set 3 (i32.xor (local.get 3) (call {index}
       (i32.add (local.get 1) (local.get 2)) (i32.xor (local.get 1) (local.get 2)) (i32.rotl (local.get 2) (i32.const 11)))))
      (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0))) (local.get 3)))'''
    m.append(q.w.parse(wrapper)[1]);q.compile(q.w.emit(m),out/r['file'])
    jobs.extend(dict(r,replicate=k) for k in range(5))
random.Random(211025).shuffle(jobs);raw=[];flags=['--no-liftoff','--no-wasm-lazy-compilation']
q.save(out/'protocol.json',dict(flags=flags,order_seed=211025,warmup=128,calibration_start=32,calibration_target_ns=10000000,calibration_max=2**22,batches=9,jobs=jobs))
for job in jobs:
    v=json.loads(subprocess.check_output(['node',*flags,str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])],text=True,timeout=60))
    raw.append(dict(job,**v));q.save(out/'runtime.json',raw)
    if len(raw)%5==0:print(json.dumps(dict(completed=len(raw),total=len(jobs))),flush=True)
summary=[]
for r in rows:
    g=[x for x in raw if x['mode']==r['mode']];med=[statistics.median(x['ns']) for x in g]
    summary.append(dict(mode=r['mode'],file=r['file'],process_medians_ns=med,median_ns=statistics.median(med),min_ns=min(med),max_ns=max(med),rss_kib_median=statistics.median(x['rss_kib'] for x in g),batch_counts=[x['batch'] for x in g]))
q.save(out/'summary.json',summary);print(json.dumps(summary))
