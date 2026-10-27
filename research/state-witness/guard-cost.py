"""Repeated analysis-cost measurements, including cached concrete BFS."""
import argparse,ctypes,hashlib,importlib.util,json,os,platform,random,shutil,statistics,subprocess,sys,time,tracemalloc
from pathlib import Path
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('witness',HERE/'guard-witness.py');w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)
def peak_rss():
    if os.name!='nt':return None
    from ctypes import wintypes as t
    class PMC(ctypes.Structure):
        _fields_=[('cb',t.DWORD),('PageFaultCount',t.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    kernel=ctypes.WinDLL('kernel32');api=ctypes.WinDLL('psapi');kernel.GetCurrentProcess.restype=t.HANDLE
    api.GetProcessMemoryInfo.argtypes=[t.HANDLE,ctypes.POINTER(PMC),t.DWORD];p=PMC();p.cb=ctypes.sizeof(p)
    if not api.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(p),p.cb):raise ctypes.WinError()
    return p.PeakWorkingSetSize
def worker(source,out,index):
    manifest=json.loads((source/'manifest.json').read_text());rows=[];rng=random.Random(7601+index)
    for row in manifest['rows']:
        if not row['name'].startswith('chain-') or int(row['name'].split('-')[-1]) not in (4,16,64,128):continue
        start=time.perf_counter();model=w.g.parse(w.k.p.read(source/row['source']));read_seconds=time.perf_counter()-start
        left,right=row['left'],row['right'];cells=model['cells'];n=len(cells);istable=cells[0]>=w.g.BASE;good,bad=(257,258) if istable else (65,66)
        build=[]
        for repeat in range(9):
            start=time.perf_counter();prepared=w.prepare(model,left,right);elapsed=time.perf_counter()-start
            if repeat>=2:build.append(elapsed)
        tracemalloc.start();tracked=w.prepare(model,left,right);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop();del tracked
        pos={i:good for i in cells};one={**pos,cells[-1]:bad}
        tail=[{c:(bad if (j>=n-5 and (v>>(j-max(0,n-5)))&1) else good) for j,c in enumerate(cells)} for v in range(32)]
        uniform=[{c:rng.choice([256,257,258]) if istable else rng.randrange(256) for c in cells} for _ in range(32)]
        datasets={'single-tail':[one],'repeated-positive':[pos.copy() for _ in range(32)],'tail-assignments':tail,'uniform':uniform};batches=[]
        for label,values in datasets.items():
            expected=[w.satisfied(prepared['proof']['guard'],v) for v in values]
            def run(method):
                cache={};got=[]
                for v in values:
                    if method=='condition':got.append(w.satisfied(prepared['proof']['guard'],v))
                    elif method=='witness':got.append(w.extract(prepared,v) is None)
                    elif method=='bfs':
                        r=w.concrete_bfs(model,left,right,v)
                        assert r['status']!='budget';got.append(r['status']=='equivalent')
                    else:
                        key=tuple(v[c] for c in cells)
                        if key in cache:r=cache[key]
                        else:r=w.concrete_bfs(model,left,right,v);cache[key]=r
                        assert r['status']!='budget';got.append(r['status']=='equivalent')
                assert got==expected
            methods=['condition','witness','bfs','cached-bfs'];times={m:[] for m in methods}
            for repeat in range(9):
                order=methods.copy();rng.shuffle(order)
                for method in order:
                    start=time.perf_counter();run(method);elapsed=time.perf_counter()-start
                    if repeat>=2:times[method].append(elapsed)
            batches.append({'distribution':label,'samples':len(values),'uniqueStores':len({tuple(v[c] for c in cells) for v in values}),
              'positive':sum(expected),'timesSeconds':times,'medianSeconds':{m:statistics.median(t) for m,t in times.items()}})
        rows.append({'name':row['name'],'cells':n,'readParseSeconds':read_seconds,'prepareSeconds':build,'prepareMedianSeconds':statistics.median(build),
          'preparePythonAllocationPeakBytes':peak,'sourceBytes':(source/row['source']).stat().st_size,'batches':batches})
        print(json.dumps({'process':index,'finished':row['name']}),flush=True)
    out.write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'processor':platform.processor(),'process':index,'seed':7601+index,
      'warmups':2,'repeats':7,'peakWorkingSetBytes':peak_rss(),'rows':rows},indent=2))
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);processes=[]
    for i in range(3):
        file=out/f'process-{i}.json';p=subprocess.run([sys.executable,str(HERE/'guard-cost.py'),str(source),str(file),'--worker',str(i)],timeout=180)
        assert p.returncode==0;processes.append(json.loads(file.read_text()))
    rows=[]
    for index,first in enumerate(processes[0]['rows']):
        sample=[p['rows'][index] for p in processes];prepare=[s['prepareMedianSeconds'] for s in sample];batches=[]
        for j,b in enumerate(first['batches']):
            ms={m:[s['batches'][j]['medianSeconds'][m] for s in sample] for m in b['medianSeconds']}
            med={m:statistics.median(v) for m,v in ms.items()};setup=statistics.median(prepare)
            batches.append({'distribution':b['distribution'],'samples':b['samples'],'uniqueStoresPerProcess':[s['batches'][j]['uniqueStores'] for s in sample],
              'processMediansSeconds':ms,'medianSeconds':med,'oneBatchTotalSeconds':{'prepared-condition':setup+med['condition'],'prepared-witness':setup+med['witness'],'bfs':med['bfs'],'cached-bfs':med['cached-bfs']}})
        rows.append({'name':first['name'],'prepareProcessMediansSeconds':prepare,'prepareMedianSeconds':statistics.median(prepare),
          'preparePythonAllocationPeakBytes':[s['preparePythonAllocationPeakBytes'] for s in sample],'batches':batches})
    result={'processes':3,'warmupsPerProcess':2,'repeatsPerProcess':7,'rows':rows,'peakWorkingSetBytes':[p['peakWorkingSetBytes'] for p in processes],
      'scope':'Artificial fixed copy chains; shared semantic effects; analysis time excludes parsing and runtime execution; witness preparation includes history reconstruction.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-cost.py','guard-witness.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--worker',type=int);v=p.parse_args()
    if v.worker is None:main(v.source,v.out)
    else:worker(v.source,v.out,v.worker)
