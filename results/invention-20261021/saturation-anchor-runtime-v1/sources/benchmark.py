import json,random,statistics,subprocess,sys
from pathlib import Path
import prototype as p

src,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False);q=p.q
rows=[r for r in json.loads((src/'manifest.json').read_text()) if r['opt']=='O3'];jobs=[]
for r in rows:
    m=q.read(src/r['file']);exports={x[1].strip('"'):int(x[2][1]) for x in m[1:] if x[0]=='export'}
    for workload in ('merge','merge_decay'):
        calls=f'(call {exports["merge"]})'
        if workload=='merge_decay':calls+=f'(call {exports["decay"]})'
        wrapper=q.w.parse(f'''(module (func (export "bench_{workload}") (param i32)
          (block (loop (br_if 1 (i32.eqz (local.get 0))) {calls}
          (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0)))))''')[1]
        m.append(wrapper)
    dst=out/r['file'];q.compile(q.w.emit(m),dst)
    jobs.extend((r,dst,w,k) for w in ('merge','merge_decay') for k in range(5))
random.Random(211001).shuffle(jobs);raw=[]
for r,dst,w,k in jobs:
    v=json.loads(subprocess.check_output(['node',str(Path(__file__).with_name('internal.cjs')),str(dst),'bench_'+w],text=True,timeout=30))
    raw.append(dict(v,file=r['file'],counters=r['counters_per_bank'],mode=r['mode'],seed=r['seed'],workload=w,replicate=k))
    q.save(out/'runtime.json',raw)
for n in (256,4096):
    for w in ('merge','merge_decay'):assert len({r['checksum'] for r in raw if r['counters']==n and r['workload']==w})==1
summary=[]
for r in rows:
    for w in ('merge','merge_decay'):
        g=[x for x in raw if x['file']==r['file'] and x['workload']==w];med=[statistics.median(x['ns']) for x in g]
        summary.append(dict(file=r['file'],counters=r['counters_per_bank'],mode=r['mode'],seed=r['seed'],workload=w,process_medians_ns=med,median_ns=statistics.median(med),min_ns=min(med),max_ns=max(med),ns_per_counter=statistics.median(med)/r['counters_per_bank'],rss_kib_median=statistics.median(x['rss_kib'] for x in g)))
q.save(out/'summary.json',summary)
print(json.dumps(dict(processes=len(raw),conditions=len(summary),checksums_match=True)))
