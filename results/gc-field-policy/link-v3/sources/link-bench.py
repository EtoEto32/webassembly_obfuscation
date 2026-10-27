import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as w
file,passes=sys.argv[1],int(sys.argv[2]);t=time.perf_counter()
c=w.Config();c.wasm_gc=True;c.wasm_function_references=True;e=w.Engine(c);s=w.Store(e)
lib=w.Instance(s,w.Module.from_file(e,file),[]).exports(s);setupMs=(time.perf_counter()-t)*1000
lib['init'](s,65536,77123)
for k in range(12):lib['run'](s,65536,passes,1,123456+k)
samples=[];checks=[]
for k in range(11):
    t=time.perf_counter();checks.append(lib['run'](s,65536,passes,1,123456+k));samples.append((time.perf_counter()-t)*1000)
print(json.dumps(dict(engine='Wasmtime',version='Python package 50.0.1',setupMs=setupMs,samples=samples,checks=checks,privateAfter=lib['private-at'](s,0))))
