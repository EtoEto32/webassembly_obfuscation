import json,random,statistics,subprocess,sys
from pathlib import Path
import prototype as p
q=p.q;src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
rows=json.loads((src/'manifest.json').read_text());selected=[r for r in rows if r['opt']=='O3' and r['mode'] in ('plain','cnf','project','project-recovered')]
manifest=[]
for row in selected:
    f=src/row['file'];m=q.read(f);n=int(next(x[2][1] for x in m[1:] if x[0]=='global'))
    body=f'''(func (param i32) (result i32) (local i32 i32)
      (local.set 1 (i32.const 123))
      (block (loop
        (br_if 1 (i32.eqz (local.get 0)))
        (i32.store (i32.const 0) (local.tee 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223))))
        (call 0)
        (local.set 2 (i32.xor (local.get 2) (i32.load (i32.const {16*n}))))
        (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0))) (local.get 2))'''
    m.append(q.w.parse('(module '+body+')')[1]);m.append(['export','"bench"',['func','1']]);dst=out/row['file'];q.compile(q.w.emit(m),dst)
    manifest.append(dict(**row,core_sha256=q.digest(f),bench_sha256=q.digest(dst),bench_bytes=dst.stat().st_size))
q.save(out/'manifest.json',manifest)
jobs=[dict(file=r['file'],kernel=r['kernel'],mode=r['mode'],repetition=k) for k in range(5) for r in selected];random.Random(211033).shuffle(jobs)
q.save(out/'protocol.json',dict(jobs=jobs,flags=['--no-liftoff','--no-wasm-lazy-compilation'],warmup=1024,batches=9,pilot_target_ns=10000000,pilot_cap=1048576,order_seed=211033,note='O3 cores, common unoptimized Wasm loop; initialization outside timing; whole-process RSS'))
results=[]
for job in jobs:
    cmd=['node','--no-liftoff','--no-wasm-lazy-compilation',str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])]
    data=json.loads(subprocess.check_output(cmd,text=True,timeout=60));results.append(dict(**job,**data));q.save(out/'runtime.json',results)
for name in {r['kernel'] for r in results}:assert len({r['checksum257'] for r in results if r['kernel']==name})==1
summary=[]
for row in selected:
    rs=[r for r in results if r['file']==row['file']];med=[statistics.median(r['ns']) for r in rs]
    summary.append(dict(kernel=row['kernel'],mode=row['mode'],core_bytes=row['bytes'],median_ns=statistics.median(med),min_process_median_ns=min(med),max_process_median_ns=max(med),maxRSSKiB=[r['maxRSSKiB'] for r in rs],linear_memory_bytes=65536))
q.save(out/'summary.json',summary)
q.save(out/'sources.json',[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in Path(__file__).parent.iterdir() if f.suffix in ('.py','.md','.cjs')])
print(json.dumps(dict(processes=len(results),conditions=len(summary),summary=summary)))
