"""Equal-output condition-only comparison, independent processes and no SMT load."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
h=load('herbrand_cost_backend','guard-herbrand.py');k=load('herbrand_cost_k','guard-import-worklist.py')
def memory():
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE;psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    item=Counters();item.cb=ctypes.sizeof(item)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(item),item.cb):raise ctypes.WinError(ctypes.get_last_error())
    return dict(workingBytes=item.WorkingSetSize,peakWorkingBytes=item.PeakWorkingSetSize)
def worker(source,out,method,index):
    rows=json.loads((source/'manifest.json').read_text())['rows'];random.Random(43961+index).shuffle(rows);records=[]
    for row in rows:
        proof=row['proof'];initial=proof['states'][0]
        summaries={(s['module'],s['field']):{key:s[key] for key in ('reads','writes')} for s in proof['hostSummaries']}
        start=time.perf_counter();model=h.i.parse(h.i.k.p.read(source/row['source']),summaries,proof.get('continuationOffsets'));parse=time.perf_counter()-start
        times=[]
        for repeat in range(7):
            start=time.perf_counter()
            if method=='generic-atomic':result=h.solve(model,initial['left'],initial['right'],proof['contract'],proof['protocol'],'atomic')
            elif method=='generic-sweep':result=h.solve(model,initial['left'],initial['right'],proof['contract'],proof['protocol'])
            else:result=k.solve(model,initial['left'],initial['right'],proof['contract'],proof['protocol'],schedule=method[2:])
            elapsed=time.perf_counter()-start
            assert all(result['proof'][key]==proof[key] for key in ('status','guard','states'))
            if repeat>=2:times.append(elapsed)
        records.append(dict(name=row['name'],length=row['length'],parseSeconds=parse,timesSeconds=times,
                            medianSeconds=statistics.median(times),memory=memory()))
    assert 'z3' not in sys.modules
    result=dict(method=method,process=index,python=sys.version,z3Loaded=False,warmups=2,repeats=5,rows=records)
    out.write_text(json.dumps(result,indent=2));print(json.dumps(dict(method=method,process=index,conditions=len(records))),flush=True)

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);processes=[];failures=[]
    methods=['generic-atomic','k-atomic','generic-sweep','k-sweep']
    for index in range(3):
        random.Random(92871+index).shuffle(methods)
        for method in methods:
            target=out/(method+'-'+str(index)+'.json')
            try:
                run=subprocess.run([sys.executable,str(Path(__file__).resolve()),str(source),str(target),'--method',method,'--worker',str(index)],timeout=180)
                if run.returncode:failures.append(dict(method=method,process=index,status='error',returncode=run.returncode))
                else:processes.append(json.loads(target.read_text()))
            except subprocess.TimeoutExpired:failures.append(dict(method=method,process=index,status='timeout'))
    comparisons=[]
    for source_row in json.loads((source/'manifest.json').read_text())['rows']:
        values={}
        for method in methods:
            samples=[next(row['medianSeconds'] for row in process['rows'] if row['name']==source_row['name']) for process in processes if process['method']==method]
            values[method]=dict(processMediansSeconds=samples,medianSeconds=statistics.median(samples) if samples else None)
        comparisons.append(dict(name=source_row['name'],length=source_row['length'],methods=values,
            genericOverKAtomic=values['generic-atomic']['medianSeconds']/values['k-atomic']['medianSeconds'] if all(v['medianSeconds'] for v in values.values()) else None))
    result=dict(rows=comparisons,processes=len(processes),failures=failures,warmups=2,repeats=5,
        scope='Artificial chains, condition-only. Same Wasm frontend; independent equality WP. Graph lowering included, parse reported separately. No Z3 loaded. Not author-tool reproduction.')
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-herbrand-cost.py','guard-herbrand.py','copy-equality.py','guard-herbrand-plan.md','guard-import-worklist.py','guard-import.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):
        shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2))
    print(json.dumps(dict(processes=len(processes),failures=failures)))
    if failures:raise SystemExit(1)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('out',type=Path);parser.add_argument('--method',choices=['generic-atomic','k-atomic','generic-sweep','k-sweep']);parser.add_argument('--worker',type=int);args=parser.parse_args()
    if args.worker is None:main(args.source,args.out)
    else:worker(args.source,args.out,args.method,args.worker)
