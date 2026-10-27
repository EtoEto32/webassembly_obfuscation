"""Read available memory and test the shared-memory binding in isolation."""
import ctypes,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(name,ctypes.c_ulonglong) for name in ('totalPhysical','availablePhysical','totalPage','availablePage','totalVirtual','availableVirtual','availableExtended')]
m=Memory();m.length=ctypes.sizeof(m)
if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):raise ctypes.WinError()
print(json.dumps({'totalPhysicalBytes':m.totalPhysical,'availablePhysicalBytes':m.availablePhysical,'enoughForSequentialOneGiB':m.availablePhysical>=3*1024**3}),flush=True)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as w
c=w.Config();c.wasm_threads=True;c.shared_memory=True;e=w.Engine(c);store=w.Store(e)
module=w.Module(e,w.wat2wasm('(module (import "env" "memory" (memory 1 1 shared)) (func (export "check") (result i32) (i32.store8 (i32.const 0) (i32.const 47)) (i32.load8_u (i32.const 0))))'))
memory=w.SharedMemory(e,module.imports[0].type)
try:w.Instance(store,module,[memory]);stock='passed'
except TypeError as err:stock=str(err)
s=importlib.util.spec_from_file_location('shared_adapter',Path(__file__).with_name('post-start-live-bindings.py'));adapter=importlib.util.module_from_spec(s);s.loader.exec_module(adapter)
memory=adapter.SharedMemory(e,module.imports[0].type);instance=w.Instance(store,module,[memory]);assert instance.exports(store)['check'](store)==47 and memory.data_ptr()[0]==47
print(json.dumps({'stockBinding':stock,'localAdapter':'passed','bytes':memory.data_len(),'readWriteValue':47}))
