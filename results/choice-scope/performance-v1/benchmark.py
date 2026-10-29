"""Fresh-process oracle latency comparison; no claim about engine speed."""
import argparse,ctypes,hashlib,json,random,shutil,statistics,subprocess,sys,time
from pathlib import Path
from oracle import Program
HERE=Path(__file__).resolve().parent
def memory():
    class PMC(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    pmc=PMC();pmc.cb=ctypes.sizeof(pmc)
    k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=ctypes.c_void_p
    fn=ctypes.windll.psapi.GetProcessMemoryInfo;fn.argtypes=[ctypes.c_void_p,ctypes.POINTER(PMC),ctypes.c_ulong]
    ok=fn(k.GetCurrentProcess(),ctypes.byref(pmc),pmc.cb)
    return dict(peakWorkingSetBytes=pmc.PeakWorkingSetSize,currentWorkingSetBytes=pmc.WorkingSetSize) if ok else dict(unavailable=True)
def worker(source,mode):
    data=json.loads((source/'node.json').read_text());cases=[];programs={}
    for r in data['rows']:
        if '-O3' in r['file'] or r['status']!='ok':continue
        if r['file'] not in programs:
            programs[r['file']]=Program(source/r['file'])
            # One fixed discriminating input from each fixture family.
            rows=[x for x in data['rows'] if x['file']==r['file']];cases.append(rows[6])
    def batch():
        qs=0
        for r in cases:
            ans=programs[r['file']].check(r['inputs'],r['outputs'],mode)
            if ans['status']!='sat':raise AssertionError(ans)
            qs+=ans['queries']
        return qs
    for _ in range(2):batch()
    samples=[];queries=[]
    for _ in range(7):
        t=time.perf_counter_ns();queries.append(batch());samples.append((time.perf_counter_ns()-t)/1e6/len(cases))
    return dict(mode=mode,cases=len(cases),warmupBatches=2,sampleBatches=7,millisecondsPerCase=samples,medianMillisecondsPerCase=statistics.median(samples),queriesPerBatch=queries,memory=memory())
def main(source,out):
    out.mkdir(parents=True,exist_ok=False)
    for f in ('oracle.py','benchmark.py'):shutil.copy2(HERE/f,out/f)
    jobs=[(mode,rep) for mode in ('joint','pointwise','independent-site','enumerated') for rep in range(3)];random.Random(20261026).shuffle(jobs);rows=[]
    for mode,rep in jobs:
        cp=subprocess.run([sys.executable,str(__file__),'--worker',str(source),mode],capture_output=True,text=True,timeout=60)
        r=dict(mode=mode,repetition=rep,code=cp.returncode,stderr=cp.stderr)
        if cp.returncode==0:r.update(json.loads(cp.stdout))
        else:r['stdout']=cp.stdout
        rows.append(r);(out/'processes.json').write_text(json.dumps(rows,indent=2))
    summary={}
    for mode in ('joint','pointwise','independent-site','enumerated'):
        group=[r for r in rows if r['mode']==mode and r['code']==0];vals=[r['medianMillisecondsPerCase'] for r in group]
        summary[mode]=dict(completedProcesses=len(group),medianOfProcessMedians=statistics.median(vals) if vals else None,processMedians=vals)
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
    (out/'manifest.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='manifest.json'},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--worker',action='store_true');ap.add_argument('source',type=Path);ap.add_argument('target');a=ap.parse_args()
    if a.worker:print(json.dumps(worker(a.source.resolve(),a.target)))
    else:main(a.source.resolve(),Path(a.target).resolve())
