import ctypes
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as w

class Counters(ctypes.Structure):
    _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(x,ctypes.c_size_t) for x in
        ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]

spec=json.loads(Path(sys.argv[1]).read_text());t=time.perf_counter()
libbytes=Path(spec['library']).read_bytes();clientbytes=Path(spec['consumer']).read_bytes()
p=subprocess.run([spec['checkerPath'],'--stdin'],input=json.dumps(dict(library=list(libbytes),consumer=list(clientbytes),policy=json.loads(Path(spec['policy']).read_text()))),capture_output=True,text=True,timeout=60)
assert p.returncode==0,p.stderr
assert next(r['accepted'] for r in json.loads(p.stdout)['results'] if r['mode']=='closure')
config=w.Config();config.wasm_gc=True;config.wasm_function_references=True
engine=w.Engine(config);store=w.Store(engine);linker=w.Linker(engine)
lib=w.Instance(store,w.Module(engine,libbytes),[]);clientmodule=w.Module(engine,clientbytes)
assert all(x.module=='lib' and x.name in spec['allowedImports'] for x in clientmodule.imports)
for name in spec['allowedImports']:linker.define(store,'lib',name,lib.exports(store)[name])
client=linker.instantiate(store,clientmodule);f=client.exports(store)['run']
setupMs=(time.perf_counter()-t)*1000;t=time.perf_counter();lib.exports(store)['init'](store,spec['n'],77123);initMs=(time.perf_counter()-t)*1000
for k in range(12):f(store,spec['n'],spec['passes'],spec['stride'],123456+k)
samples=[];checks=[]
for k in range(11):
    t=time.perf_counter();checks.append(f(store,spec['n'],spec['passes'],spec['stride'],123456+k));samples.append((time.perf_counter()-t)*1000)
c=Counters();c.cb=ctypes.sizeof(c)
ctypes.windll.kernel32.GetCurrentProcess.restype=ctypes.c_void_p
ctypes.windll.psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
assert ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(c),c.cb)
print(json.dumps(dict(engine='Wasmtime',version='Python package 50.0.1',setupMs=setupMs,initMs=initMs,samples=samples,checks=checks,
    peakBytes=c.PeakWorkingSetSize,privateAfter=lib.exports(store)['private-at'](store,0))))
