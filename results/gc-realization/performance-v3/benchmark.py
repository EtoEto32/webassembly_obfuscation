"""Repeated generation cost and complete build+verify guest cost; no speedup assumption."""
import argparse,json,platform,statistics,subprocess,sys,time,tracemalloc,shutil
from pathlib import Path
from realize import HERE,ROOT,generate
from experiment import model,dump,digest,wt

def cases():
    result=[]
    for n in [8,16,32]:
        result.append(dict(name='nonnull-ring-%d'%n,model=model('array',True,False),nodes=[dict(type=0,values=[dict(node=(i+1)%n)]) for i in range(n)]))
        result.append(dict(name='immutable-chain-%d'%n,model=model('array',False,False),nodes=[dict(type=0,values=[] if i==0 else [dict(node=i-1)]) for i in range(n)]))
    return result

def worker(mode):
    cs=cases();samples=[]
    for batch in range(12):
        start=time.perf_counter_ns()
        for _ in range(10):
            for c in cs:generate(c['model'],c['nodes'],mode)
        elapsed=(time.perf_counter_ns()-start)/1e6/(10*len(cs))
        if batch>=3:samples.append(elapsed)
    tracemalloc.start()
    for c in cs:generate(c['model'],c['nodes'],mode)
    peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
    print(json.dumps(dict(mode=mode,samples_ms=samples,median_ms=statistics.median(samples),python_peak_bytes=peak)))

def main(out):
    out.mkdir(parents=True,exist_ok=False);requests={};sizes=[]
    for mode in ['staged','dfs-staged']:
        files=[]
        for c in cases():
            g=generate(c['model'],c['nodes'],mode,return_nodes=True);p=out/(c['name']+'-'+mode+'.wasm');p.write_bytes(wt.wat2wasm(g['wat']));observer=p.with_name(p.stem+'-observer.wasm');observer.write_bytes(wt.wat2wasm(g['observer_wat']));files.append(dict(file=p.name,observer=observer.name,nodes=len(c['nodes'])));sizes.append(dict(name=c['name'],mode=mode,bytes=p.stat().st_size,observer_bytes=observer.stat().st_size,helpers=g['helper_allocations'],patches=g['patches'],checks=g['checks']))
        request=out/(mode+'-request.json');dump(request,dict(directory=str(out.resolve()),files=files));requests[mode]=request
    rows=[];guest=[]
    for rep in range(3):
        modes=['staged','dfs-staged'] if rep%2==0 else ['dfs-staged','staged']
        for mode in modes:
            p=subprocess.run([sys.executable,str(Path(__file__)),'--worker',mode],capture_output=True,text=True,timeout=60);p.check_returncode();rows.append(dict(rep=rep,**json.loads(p.stdout)))
            p=subprocess.run(['node',str(HERE/'benchmark.cjs'),str(requests[mode])],capture_output=True,text=True,timeout=60);p.check_returncode();guest.append(dict(rep=rep,mode=mode,**json.loads(p.stdout)))
    summary={}
    for mode in requests:
        rs=[r for r in rows if r['mode']==mode];vs=[r['median_ms'] for r in rs];gs=[r for r in guest if r['mode']==mode]
        summary[mode]=dict(median_generation_ms=statistics.median(vs),process_medians_ms=vs,python_peak_bytes=[r['python_peak_bytes'] for r in rs],guest_peak_RSS_KiB=[r['peakRSSKiB'] for r in gs],guest_case_medians_ns={c['name']:statistics.median(next(x for x in r['cases'] if x['file']==c['name']+'-'+mode+'.wasm')['median_ns'] for r in gs) for c in cases()})
    dump(out/'generation.json',rows);dump(out/'guest.json',guest);dump(out/'sizes.json',sizes);dump(out/'summary.json',summary);dump(out/'settings.json',dict(platform=platform.platform(),python=sys.version,generation_warmup_batches=3,generation_measurement_batches=9,plans_per_batch=60,fresh_processes_per_mode=3,guest_warmup_calls_per_case=200,guest_measurement_batches=7,guest_calls_per_batch=500,guest_includes_all_identity_checks=True,all_nodes_escape_to_JS=True,separate_observer_module=True,cross_call_root_identity_checked=True))
    for p in [Path(__file__),HERE/'benchmark.cjs',HERE/'realize.py']:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(summary,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path,nargs='?');ap.add_argument('--worker');a=ap.parse_args();worker(a.worker) if a.worker else main(a.out)
