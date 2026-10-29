import json, random, statistics, subprocess, sys
from pathlib import Path
import prototype as p

src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=False)
rows=[r for r in json.loads((src/'manifest.json').read_text()) if r['opt']=='O3']
wrapper=p.q.w.parse('''(module (func (export "bench") (param i32 i32 i32 i32) (result i32)
 (block (loop (br_if 1 (i32.eqz (local.get 0)))
  (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
  (local.set 3 (call 0 (local.get 1) (i32.xor (local.get 1) (local.get 2)) (local.get 3)))
  (local.set 2 (i32.add (local.get 2) (local.get 3)))
  (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0))) (local.get 3)))''')[1]
jobs=[]
for r in rows:
    m=p.q.read(src/r['file']);m.append(wrapper);dst=out/r['file'];p.q.compile(p.q.w.emit(m),dst)
    jobs.extend((r,dst,k) for k in range(5))
random.Random(21102026).shuffle(jobs);raw=[]
for r,dst,k in jobs:
    v=json.loads(subprocess.check_output(['node',str(p.ROOT/'research/encoding-lowering/internal.cjs'),str(dst)],text=True,timeout=30))
    raw.append(dict(v,kernel=r['kernel'],mode=r['mode'],seed=r['seed'],file=r['file'],replicate=k))
    p.q.save(out/'runtime.json',raw)
for kernel in sorted({r['kernel'] for r in rows}):
    assert len({r['checksum'] for r in raw if r['kernel']==kernel})==1, kernel
summary=[]
for r in rows:
    group=[x for x in raw if x['file']==r['file']];med=[statistics.median(x['ns']) for x in group]
    summary.append(dict(file=r['file'],kernel=r['kernel'],mode=r['mode'],seed=r['seed'],process_medians=med,median_ns=statistics.median(med),min_ns=min(med),max_ns=max(med)))
p.q.save(out/'summary.json',summary)
print(json.dumps({'processes':len(raw),'conditions':len(rows),'checksums_match':True}))
