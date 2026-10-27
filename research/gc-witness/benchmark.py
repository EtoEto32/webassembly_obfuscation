"""Sequential fresh processes; planning/code emission only, not guest runtime."""
import argparse,json,statistics,subprocess,sys,time,tracemalloc,shutil
from pathlib import Path
from experiment import HERE,dump,digest
from witness import generate
def worker(source,mode):
    ms=json.loads((source/'models.json').read_text());names=['chain-1-21','chain-2-9','chain-4-5','self-array','array-breaks-cycle']
    models={m['name']:m['model'] for m in ms};cases=[(models[n],len(models[n]['types'])-1,[]) for n in names]+[(models['self-array'],0,['e']*12)]
    def batch():
        for _ in range(20):
            for m,t,p in cases:generate(m,t,p,mode,node_budget=2048,depth_budget=64)
    for _ in range(3):batch()
    times=[]
    for _ in range(9):t=time.perf_counter_ns();batch();times.append((time.perf_counter_ns()-t)/1e6/(20*len(cases)))
    tracemalloc.start();batch();_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    return dict(mode=mode,batch_ms_per_plan=times,median_ms_per_plan=statistics.median(times),python_traced_peak_bytes=peak,plans_per_batch=20*len(cases),warmup_batches=3,measured_batches=9,cases=names+['self-array path e*12'])
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for repeat in range(3):
        for mode in ['tree','memo','worklist'][repeat:]+['tree','memo','worklist'][:repeat]:
            cp=subprocess.run([sys.executable,str(HERE/'benchmark.py'),str(source),'--worker',mode],capture_output=True,text=True,timeout=60);cp.check_returncode();rows.append(dict(repeat=repeat,**json.loads(cp.stdout)))
    summary={m:dict(process_medians_ms=[r['median_ms_per_plan'] for r in rows if r['mode']==m],median_ms=statistics.median(r['median_ms_per_plan'] for r in rows if r['mode']==m),peak_python_bytes=[r['python_traced_peak_bytes'] for r in rows if r['mode']==m]) for m in ['tree','memo','worklist']}
    dump(out/'rows.json',rows);dump(out/'summary.json',summary);shutil.copy2(HERE/'benchmark.py',out/'benchmark.py');dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.iterdir() if p.is_file()]);print(json.dumps(summary,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path,nargs='?');ap.add_argument('--worker',choices=['tree','memo','worklist']);a=ap.parse_args()
    if a.worker:print(json.dumps(worker(a.source,a.worker)))
    else:main(a.source,a.out)
