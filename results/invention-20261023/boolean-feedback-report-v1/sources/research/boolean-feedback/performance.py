import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
from shared import h,load
saved=sys.modules.get('prototype');sys.modules['prototype']=h
previous=load('bf_wrapper',h.HERE.parent/'span-mask/performance.py')
if saved is None:del sys.modules['prototype']
else:sys.modules['prototype']=saved


def main(base,out,modes=('plain','pipeline','feedback')):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);targets=[]
    for name in ('mix8','select10','chain12'):
        for mode in modes:
            src=base/(name+'-'+mode+'-O3.wasm');dest=out/(src.stem+'-bench.wasm');previous.wrapper(src,2,dest);targets.append({'name':name,'mode':mode,'file':dest.name,'core_bytes':src.stat().st_size,'memory_bytes':0 if mode=='plain' else 65536})
    order=[(i,j) for i in range(len(targets)) for j in range(3)];random.Random(20261023).shuffle(order);rows=[]
    for i,rep in order:
        t=targets[i];r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(h.HERE.parent/'span-mask/bench.cjs'),str(out/t['file'])],capture_output=True,text=True,timeout=120)
        (out/(t['name']+'-'+t['mode']+'-'+str(rep)+'.stdout.log')).write_text(r.stdout)
        (out/(t['name']+'-'+t['mode']+'-'+str(rep)+'.stderr.log')).write_text(r.stderr)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append({**t,'repetition':rep,**json.loads(r.stdout)});(out/'raw.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'done':len(rows),'name':t['name'],'mode':t['mode']}),flush=True)
    summary=[]
    for t in targets:
        r=[v for v in rows if v['file']==t['file']];medians=[statistics.median(v['ns_per_call']) for v in r]
        summary.append({**t,'median_ns':statistics.median(medians),'process_medians_ns':medians,'rss_kib':[v['max_rss_kib'] for v in r],'batch_min_ns':min(x for v in r for x in v['ns_per_call']),'batch_max_ns':max(x for v in r for x in v['ns_per_call'])})
    (out/'summary.json').write_text(json.dumps({'targets':summary,'processes':len(rows),'batches':7*len(rows),'batches_under_10ms':sum(b['ms']<10 for v in rows for b in v['batches'])},indent=2));(out/'pins.json').write_text(json.dumps({str(f.relative_to(h.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='pins.json'},indent=2))

if __name__=='__main__':main(*sys.argv[1:])
