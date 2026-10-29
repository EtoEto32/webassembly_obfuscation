"""One actual ffmpeg module per process, with shared memory kept quiescent."""
import argparse,ctypes,hashlib,importlib.util,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
s=importlib.util.spec_from_file_location('live_shared',HERE/'post-start-live-bindings.py');adapter=importlib.util.module_from_spec(s);s.loader.exec_module(adapter)

def main(source,variant,out):
    meta=json.loads((source/'manifest.json').read_text());raw=(source/('observed-'+variant+'.wasm')).read_bytes();config=wt.Config();config.wasm_threads=True;config.shared_memory=True
    engine=wt.Engine(config);started=time.perf_counter();module=wt.Module(engine,raw);compiled=time.perf_counter()-started;import_calls=0
    with wt.Store(engine) as store:
        memories=[];imports=[]
        def forbidden(*args):
            nonlocal import_calls
            import_calls+=1;raise RuntimeError('unexpected host call in actual start/probes')
        for imp in module.imports:
            if isinstance(imp.type,wt.FuncType):imports.append(wt.Func(store,imp.type,forbidden))
            elif isinstance(imp.type,wt.MemoryType):
                assert imp.type.is_shared;memory=adapter.SharedMemory(engine,imp.type);imports.append(memory);memories.append(memory)
            else:raise ValueError('unexpected import type')
        started=time.perf_counter();ex=wt.Instance(store,module,imports).exports(store);instantiated=time.perf_counter()-started;assert import_calls==0 and len(memories)==1
        memory=memories[0];length=memory.data_len();buffer=(ctypes.c_ubyte*length).from_address(ctypes.addressof(memory.data_ptr().contents))
        before=hashlib.sha256(buffer).hexdigest();pure=[];outcomes=[]
        for item in meta['pureConstantExports']:
            value=ex[item['name']](store);assert value==item['value'];pure.append({'name':item['name'],'value':value})
        for segment in range(len(meta['dataLengths'])):
            try:assert ex[meta['probePrefix']+str(segment)](store)==1;outcomes.append('live')
            except wt.Trap:outcomes.append('trap')
        after=hashlib.sha256(buffer).hexdigest();assert before==after and import_calls==0
        assert all(v==('trap' if variant=='original' else 'live') for v in outcomes)
        result={'variant':variant,'engine':'Wasmtime','version':'50.0.1','python':sys.version,'bindingAdapter':'local corrected _as_extern pointer; dependency files unchanged',
            'wasmSha256':hashlib.sha256(raw).hexdigest(),'compileMs':compiled*1000,'instantiateMs':instantiated*1000,'memoryBytes':length,'memoryBefore':before,'memoryAfter':after,
            'tableSizes':[{'name':name,'length':value.size(store)} for name,value in ex.items() if isinstance(value,wt.Table)],'pureConstantExports':pure,'originalApiCalls':len(pure),
            'probeCalls':len(outcomes),'live':outcomes.count('live'),'traps':outcomes.count('trap'),'importCalls':import_calls,'outcomes':outcomes}
    out.write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ('engine','variant','live','traps','originalApiCalls','memoryBefore')}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('variant',choices=['original','retained']);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.variant,v.out)
