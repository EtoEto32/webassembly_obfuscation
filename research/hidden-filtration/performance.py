import hashlib
import importlib.util
import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import prototype as p

sp=importlib.util.spec_from_file_location('hfl_bench_wrapper',p.HERE.parent/'span-mask/performance.py')
previous=importlib.util.module_from_spec(sp);sp.loader.exec_module(previous)


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    targets=[]
    for name in ('mix8','select10','chain12'):
        for mode in ('plain','pipeline','linear','nonlinear'):
            src=base/(name+'-'+mode+'-O3.wasm');dest=out/(name+'-'+mode+'-bench.wasm');previous.wrapper(src,2,dest)
            targets.append({'name':name,'mode':mode,'file':dest.name,'core_bytes':src.stat().st_size,'linear_memory_bytes':0 if mode=='plain' else 65536})
    order=[(j,r) for j in range(len(targets)) for r in range(3)];random.Random(20261023).shuffle(order);records=[]
    for j,rep in order:
        t=targets[j];r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.HERE.parent/'span-mask/bench.cjs'),str(out/t['file'])],capture_output=True,text=True,timeout=120)
        label=f'{t["name"]}-{t["mode"]}-{rep}';(out/(label+'.stdout.log')).write_text(r.stdout);(out/(label+'.stderr.log')).write_text(r.stderr)
        if r.returncode:raise RuntimeError(r.stderr)
        value=json.loads(r.stdout);records.append({**t,'repetition':rep,**value});(out/'raw.json').write_text(json.dumps(records,indent=2))
        print(json.dumps({'done':len(records),'name':t['name'],'mode':t['mode'],'median_ns':statistics.median(value['ns_per_call'])}),flush=True)
    rows=[]
    for t in targets:
        rs=[r for r in records if r['file']==t['file']];medians=[statistics.median(r['ns_per_call']) for r in rs]
        rows.append({**t,'median_ns':statistics.median(medians),'process_medians_ns':medians,'batch_min_ns':min(v for r in rs for v in r['ns_per_call']),'batch_max_ns':max(v for r in rs for v in r['ns_per_call']),'rss_kib':[r['max_rss_kib'] for r in rs]})
    summary={'targets':rows,'processes':len(records),'batches':7*len(records),'batches_under_10ms':sum(b['ms']<10 for r in records for b in r['batches'])}
    (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'pins.json').write_text(json.dumps({str(f.relative_to(p.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='pins.json'},indent=2))


if __name__=='__main__':main(*sys.argv[1:])
