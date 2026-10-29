import ctypes
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as w

class Counters(ctypes.Structure):
    _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(x,ctypes.c_size_t) for x in
        ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]

file,n=sys.argv[1],int(sys.argv[2])
t=time.perf_counter()
config=w.Config();config.wasm_tail_call=True
engine=w.Engine(config);store=w.Store(engine);module=w.Module.from_file(engine,file)
gate=w.Global(store,w.GlobalType(w.ValType.i32(),True),1)
instance=w.Instance(store,module,[gate] if len(module.imports) else [])
f=instance.exports(store)['run'];setupMs=(time.perf_counter()-t)*1000
for k in range(12):f(store,n,123456+k)
samples=[];checks=[]
for k in range(11):
    t=time.perf_counter();checks.append(f(store,n,123456+k));samples.append((time.perf_counter()-t)*1000)
c=Counters();c.cb=ctypes.sizeof(c)
ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
assert ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(c),c.cb)
print(json.dumps(dict(engine='Wasmtime',version='Python package 50.0.1',n=n,setupMs=setupMs,samples=samples,checks=checks,peakBytes=c.PeakWorkingSetSize)))
