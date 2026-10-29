"""Repeated same-output synthesis measurements, sequential isolated workers."""
import argparse,ctypes,hashlib,importlib.util,json,os,platform,random,shutil,statistics,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cost_generic',HERE/'guard-import-generic.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.q.i


def memory():
    if os.name!='nt':return None
    from ctypes import wintypes as t
    class PMC(ctypes.Structure):
        _fields_=[('cb',t.DWORD),('PageFaultCount',t.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    kernel=ctypes.WinDLL('kernel32');api=ctypes.WinDLL('psapi');kernel.GetCurrentProcess.restype=t.HANDLE;api.GetProcessMemoryInfo.argtypes=[t.HANDLE,ctypes.POINTER(PMC),t.DWORD]
    p=PMC();p.cb=ctypes.sizeof(p)
    if not api.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(p),p.cb):raise ctypes.WinError()
    return {'peakWorkingSetBytes':p.PeakWorkingSetSize,'workingSetBytes':p.WorkingSetSize}


def worker(source,out,method,index):
    rows=json.loads((source/'manifest.json').read_text())['rows'];rng=random.Random(17651+index);rng.shuffle(rows);results=[]
    for row in rows:
        summaries={(s['module'],s['field']):{k:s[k] for k in ('reads','writes')} for s in row['proof']['hostSummaries']}
        started=time.perf_counter();model=i.parse(i.k.p.read(source/row['source']),summaries);parse=time.perf_counter()-started;times=[];before=memory()
        for repeat in range(7):
            result=None;started=time.perf_counter()
            if method=='specialized':result=i.prepare(model,row['left'],row['right'],row['proof']['contract'],row['proof']['protocol'])
            else:result=b.solve(model,row['left'],row['right'],row['proof']['contract'],row['proof']['protocol'])
            elapsed=time.perf_counter()-started
            if repeat>=2:times.append(elapsed)
        after=memory()
        if method=='specialized':assert result['proof']['guard']==row['proof']['guard']
        else:
            z=b.z;solver=z.Solver();solver.set(timeout=5000);solver.add(result['domain'],result['formula']!=b.q.a.a.predicate(row['proof']['guard'],result['left'],result['left']));assert solver.check()==z.unsat
        results.append({'name':row['name'],'length':row['length'],'parseSeconds':parse,'timesSeconds':times,'medianSeconds':statistics.median(times),'memoryBefore':before,'memoryAfter':after})
        print(json.dumps({'method':method,'process':index,'case':row['name'],'medianSeconds':statistics.median(times)}),flush=True)
    result={'method':method,'process':index,'seed':17651+index,'python':sys.version,'platform':platform.platform(),'processor':platform.processor(),'z3':b.z.get_version_string(),
        'warmups':2,'repeats':5,'memory':memory(),'rows':results}
    out.write_text(json.dumps(result,indent=2))


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);processes=[];failures=[]
    for index in range(3):
        for method in ('specialized','generic'):
            target=out/(method+'-'+str(index)+'.json')
            try:
                run=subprocess.run([sys.executable,str(Path(__file__).resolve()),str(source),str(target),'--method',method,'--worker',str(index)],timeout=180)
                if run.returncode:failures.append({'method':method,'process':index,'status':'worker-error','code':run.returncode})
                else:processes.append(json.loads(target.read_text()))
            except subprocess.TimeoutExpired:failures.append({'method':method,'process':index,'status':'worker-timeout'})
    rows=[]
    names=[r['name'] for r in json.loads((source/'manifest.json').read_text())['rows']]
    for name in names:
        methods={}
        for method in ('specialized','generic'):
            cases=[next(r for r in p['rows'] if r['name']==name) for p in processes if p['method']==method]
            medians=[c['medianSeconds'] for c in cases]
            methods[method]={'processMediansSeconds':medians,'medianSeconds':statistics.median(medians) if medians else None,'rangeSeconds':[min(medians),max(medians)] if medians else None,
                'parseSeconds':[c['parseSeconds'] for c in cases],'memoryBefore':[c['memoryBefore'] for c in cases],'memoryAfter':[c['memoryAfter'] for c in cases]}
        rows.append({'name':name,'methods':methods,'specializedOverGeneric':methods['specialized']['medianSeconds']/methods['generic']['medianSeconds'] if all(m['medianSeconds'] for m in methods.values()) else None})
    result={'rows':rows,'processes':len(processes),'failures':failures,'warmups':2,'repeats':5,'scope':'Artificial delayed table-copy chains. Same condition-generation task, shared parsing excluded and reported separately. Both workers load Z3. Memory is whole-process, cumulative peak.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-import-cost.py','guard-import-cost-plan.md','guard-import-generic.py','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({'processes':len(processes),'failures':failures}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);a.add_argument('--method',choices=['generic','specialized']);a.add_argument('--worker',type=int);v=a.parse_args()
    if v.worker is None:main(v.source,v.out)
    else:worker(v.source,v.out,v.method,v.worker)
