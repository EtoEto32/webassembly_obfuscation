import json
import random
import statistics
import subprocess
import sys
from pathlib import Path
import prototype as p

main,out=map(lambda x:Path(x).resolve(),sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
rows=[r for r in json.loads((main/'manifest.json').read_text()) if r['opt']=='O3' and r['mode']!='recovered']
jobs=[dict(row,replicate=i) for row in rows for i in range(3)]
random.Random(21102196).shuffle(jobs);records=[]
flags=['--no-liftoff','--no-wasm-lazy-compilation']
for job in jobs:
    proc=subprocess.run(['node',*flags,str(Path(__file__).with_name('bench.cjs')),str(main/job['file']),
                         str(main/(job['name']+'-source-O3.wasm'))],capture_output=True,text=True,timeout=60)
    proc.check_returncode();records.append(dict(job,**json.loads(proc.stdout)));p.q.save(out/'runtime.json',records)
summary=[]
for row in rows:
    rs=[r for r in records if r['file']==row['file']];medians=[statistics.median(r['ns']) for r in rs]
    summary.append(dict(file=row['file'],name=row['name'],mode=row['mode'],bytes=row['bytes'],
                        median_ns=statistics.median(medians),process_medians_ns=medians,rss_kib=[r['rss_kib'] for r in rs],
                        history=row['transform']['history'],batch_calls=[r['batch'] for r in rs]))
p.q.save(out/'summary.json',summary)
p.q.save(out/'protocol.json',dict(processes=len(jobs),flags=flags,order_seed=21102196,input_seed=21102195,
                                  words=128,warmup=1024,target_ms=5,batches=9,max_calls=2**18,
                                  timing_includes='JS call loop and checksum; no compilation/instantiation'))
print(json.dumps(dict(processes=len(jobs),conditions=len(summary))))
