import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import prototype as p


def main(main_dir,dest):
    folder=Path(main_dir).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    variants=[t for t in manifest['targets'] if t['opt']=='O3' and t['mode'] in ('plain','basis','side') and t['seed'] in (0,211070)]
    wrapper=out/'wrapper.wasm'
    p.q.compile('''(module (import "target" "run" (func (param i32))) (import "target" "digest" (func (result i32)))
      (func (export "bench") (param i32) (result i32)
        (block (loop (br_if 1 (i32.eqz (local.get 0)))
          (call 0 (i32.add (local.get 0) (i32.const 32)))
          (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0))) (call 1)))''',wrapper)
    schedule=[(v,i) for v in variants for i in range(3)];random.Random(20261024).shuffle(schedule);rows=[]
    for t,i in schedule:
        proc=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.ROOT/'research/loss-flag/bench.cjs'),str(folder/t['file']),str(wrapper)],capture_output=True,text=True,timeout=60)
        if proc.returncode:raise RuntimeError(proc.stderr)
        rows.append(dict(name=t['name'],mode=t['mode'],file=t['file'],bytes=t['bytes'],repeat=i,measurement=json.loads(proc.stdout)))
        p.q.save(out/'raw.json',rows)
        if len(rows)%9==0:print('processes',len(rows),flush=True)
    summary=[]
    for t in variants:
        procs=[x['measurement'] for x in rows if x['file']==t['file']];medians=[statistics.median(b['ns_per_run'] for b in x['batches']) for x in procs]
        values=[b['ns_per_run'] for x in procs for b in x['batches']]
        summary.append(dict(name=t['name'],mode=t['mode'],core_bytes=t['bytes'],median_ns=statistics.median(medians),process_medians=medians,min_ns=min(values),max_ns=max(values),max_rss_kib=max(x['max_rss_kib'] for x in procs),linear_memory_bytes=65536))
    result=dict(rows=summary,processes=len(rows),batches=sum(len(x['measurement']['batches']) for x in rows),under_10ms=sum(b['ns']<10e6 for x in rows for b in x['measurement']['batches']))
    p.q.save(out/'summary.json',result);print(json.dumps(result))


if __name__=='__main__':main(*sys.argv[1:])
