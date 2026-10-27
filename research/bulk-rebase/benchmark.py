"""Fixed-protocol, sequential fresh-process copy benchmark."""
import json,random,statistics,subprocess,sys
from pathlib import Path
import prototype as p

src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);q=p.q
rows=[r for r in json.loads((src/'manifest.json').read_text()) if r['opt']=='O3' and r['pages']==1 and r['seed']==(0 if r['mode']=='plain' else 7)]
assert len(rows)==6
layouts={'forward':(1024,1027),'backward':(1027,1024),'separate':(16385,1024)}
jobs=[]
for r in rows:
    m=q.read(src/r['file'])
    exports={x[1].strip('"'):int(x[2][1]) for x in m[1:] if x[0]=='export' and x[2][0]=='func'}
    m.append(p.expr(f'''(func (export "bench") (param i32 i32 i32 i32)
      (block (loop (br_if 1 (i32.eqz (local.get 0)))
        (call {exports['copy']} (local.get 1) (local.get 2) (local.get 3))
        (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0))))'''))
    f=out/r['file'];q.compile(q.w.emit(m),f)
    jobs.extend(dict(file=r['file'],mode=r['mode'],n=n,layout=layout,d=d,s=s,replicate=k) for n in (16,256,4096) for layout,(d,s) in layouts.items() for k in range(5))
random.Random(211024).shuffle(jobs)
flags=['--no-liftoff','--no-wasm-lazy-compilation']
q.save(out/'protocol.json',dict(order_seed=211024,jobs=jobs,node_flags=flags,warmup_bytes=262144,batch_bytes=1048576,batches=9,processes=len(jobs),measurement='copy-only; fill/checksum excluded; O3 target plus common loop, no later wasm-opt',source_manifest_sha256=q.digest(src/'manifest.json')))
raw=[]
for job in jobs:
    v=json.loads(subprocess.check_output(['node',*flags,str(Path(__file__).with_name('bench.cjs')),str(out/job['file']),str(job['d']),str(job['s']),str(job['n'])],text=True,timeout=40))
    raw.append(dict(job,**v));q.save(out/'runtime.json',raw)
    if len(raw)%30==0:print(json.dumps(dict(completed=len(raw),total=len(jobs))),flush=True)
for n in (16,256,4096):
    for layout in layouts:assert len({r['checksum'] for r in raw if r['n']==n and r['layout']==layout})==1,(n,layout)
summary=[]
for r in rows:
    for n in (16,256,4096):
        for layout in layouts:
            g=[x for x in raw if x['file']==r['file'] and x['n']==n and x['layout']==layout]
            med=[statistics.median(x['ns']) for x in g]
            summary.append(dict(file=r['file'],mode=r['mode'],n=n,layout=layout,process_medians_ns=med,median_ns=statistics.median(med),min_ns=min(med),max_ns=max(med),rss_kib_median=statistics.median(x['rss_kib'] for x in g),instantiate_ms_median=statistics.median(x['instantiate_ms'] for x in g)))
q.save(out/'summary.json',summary)
print(json.dumps(dict(processes=len(raw),conditions=len(summary),checksums_match=True)))
