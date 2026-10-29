import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import prototype as p
common=p.load('rotor_common_performance',p.HERE.parent/'span-mask/performance.py')

def main(base,out,modes=('plain','rotor','recovered')):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);targets=[]
    for name in ('and3','majority3','mux3'):
        for mode in modes:
            src=base/(name+'-'+('O3-recovered-O3' if mode=='recovered' else mode+'-O3')+'.wasm')
            if not src.exists():continue
            dest=out/(name+'-'+mode+'-bench.wasm');common.wrapper(src,3,dest)
            targets.append({'name':name,'mode':mode,'file':dest.name,'core_bytes':src.stat().st_size,'memory_bytes':65536 if mode=='rotor' else 0})
    schedule=[(i,j) for i in range(len(targets)) for j in range(3)];random.Random(20261023).shuffle(schedule);rows=[]
    for i,rep in schedule:
        t=targets[i];r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.HERE.parent/'span-mask/bench.cjs'),str(out/t['file'])],capture_output=True,text=True,timeout=120)
        label=t['name']+'-'+t['mode']+'-'+str(rep);(out/(label+'.stdout.txt')).write_text(r.stdout);(out/(label+'.stderr.txt')).write_text(r.stderr)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append({**t,'repetition':rep,**json.loads(r.stdout)});(out/'raw.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'done':len(rows),'name':t['name'],'mode':t['mode']}),flush=True)
    summary=[]
    for t in targets:
        rs=[r for r in rows if r['file']==t['file']];medians=[statistics.median(r['ns_per_call']) for r in rs]
        summary.append({**t,'median_ns':statistics.median(medians),'process_medians_ns':medians,'rss_kib':[r['max_rss_kib'] for r in rs]})
    (out/'summary.json').write_text(json.dumps({'targets':summary,'processes':len(rows),'batches':7*len(rows),'batches_under_10ms':sum(b['ms']<10 for r in rows for b in r['batches'])},indent=2))

if __name__=='__main__':main(sys.argv[1],sys.argv[2],tuple(sys.argv[3:]) or ('plain','rotor','recovered'))
