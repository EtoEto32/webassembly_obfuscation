"""Matched Wasm wrapper, three fresh V8 processes and seven batches per core."""
import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import performance as common
from shared import h


def main(base,attacks,out):
    base=Path(base).resolve();attacks=Path(attacks).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);targets=[]
    for name in ('muladd','square','mixcarry'):
        for mode in ('plain','pipeline','feedback','recovered'):
            src=base/(name+'-'+mode+('' if mode=='plain' else '-0')+'-O3.wasm')
            if mode=='recovered':src=attacks/(name+'-O3-recovered-O3.wasm')
            dest=out/(name+'-'+mode+'-bench.wasm');common.previous.wrapper(src,3,dest)
            targets.append({'name':name,'mode':mode,'file':dest.name,'core_bytes':src.stat().st_size,'memory_bytes':0})
    order=[(i,j) for i in range(len(targets)) for j in range(3)];random.Random(20261023).shuffle(order);rows=[]
    for i,rep in order:
        t=targets[i];r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(h.HERE.parent/'span-mask/bench.cjs'),str(out/t['file'])],capture_output=True,text=True,timeout=120)
        label=t['name']+'-'+t['mode']+'-'+str(rep);(out/(label+'.stdout.log')).write_text(r.stdout);(out/(label+'.stderr.log')).write_text(r.stderr)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append({**t,'repetition':rep,**json.loads(r.stdout)});(out/'raw.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'done':len(rows),'name':t['name'],'mode':t['mode']}),flush=True)
    summary=[]
    for t in targets:
        r=[v for v in rows if v['file']==t['file']];medians=[statistics.median(v['ns_per_call']) for v in r]
        summary.append({**t,'median_ns':statistics.median(medians),'process_medians_ns':medians,'rss_kib':[v['max_rss_kib'] for v in r],
                        'batch_min_ns':min(x for v in r for x in v['ns_per_call']),'batch_max_ns':max(x for v in r for x in v['ns_per_call'])})
    (out/'summary.json').write_text(json.dumps({'targets':summary,'processes':len(rows),'batches':7*len(rows),'batches_under_10ms':sum(b['ms']<10 for v in rows for b in v['batches'])},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
