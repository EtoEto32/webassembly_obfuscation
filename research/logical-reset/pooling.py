"""Native-loop Wasmtime pooling comparison; no Python dispatch inside timed loop."""
import argparse,ctypes as c,hashlib,importlib.metadata,json,platform,random,shutil,statistics,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt
from wasmtime import _ffi as ffi

def engine(kind):
    cfg=wt.Config()
    if kind!='on-demand':
        pc=ffi.wasmtime_pooling_allocation_config_new()
        for suffix,val in [('total_memories',4),('total_tables',4),('total_core_instances',4),
                           ('total_component_instances',0),('total_gc_heaps',0),('total_stacks',0),
                           ('max_memory_size',16*1024*1024),('table_elements',4096)]:
            getattr(ffi,'wasmtime_pooling_allocation_config_'+suffix+'_set')(pc,val)
        if kind=='pooling-compact':
            ffi.wasmtime_config_memory_reservation_set(cfg.ptr(),16*1024*1024)
            ffi.wasmtime_config_memory_guard_size_set(cfg.ptr(),0)
            ffi.wasmtime_config_memory_init_cow_set(cfg.ptr(),False)
            ffi.wasmtime_pooling_allocation_config_linear_memory_keep_resident_set(pc,16*1024*1024)
            ffi.wasmtime_pooling_allocation_config_table_keep_resident_set(pc,4096*8)
        ffi.wasmtime_pooling_allocation_strategy_set(cfg.ptr(),pc)
        ffi.wasmtime_pooling_allocation_config_delete(pc)
    return wt.Engine(cfg)

def child(source,dll,seed):
    # Numeric layouts are validated before the native harness interprets buffers.
    assert ffi.wasmtime_val_t.of.offset==8 and ffi.wasmtime_extern_t.of.offset==8
    assert c.sizeof(ffi.wasmtime_func_t)==16
    assert max(c.sizeof(t) for t in [ffi.wasmtime_val_t,ffi.wasmtime_extern_t,ffi.wasmtime_instance_t])<=128
    lib=c.CDLL(str(dll.resolve()));lib.measure.restype=c.c_double
    lib.measure.argtypes=[c.POINTER(c.c_size_t),c.c_void_p,c.c_void_p,c.c_size_t,c.c_int32,c.c_bool,c.c_int32]
    names=['wasmtime_store_new','wasmtime_store_context','wasmtime_store_delete','wasmtime_instance_new',
           'wasmtime_instance_export_get','wasmtime_func_call','wasmtime_error_delete','wasm_trap_delete','wasmtime_extern_delete']
    api=(c.c_size_t*len(names))(*[c.cast(getattr(ffi.dll,n),c.c_void_p).value for n in names])
    manifest=json.loads((source/'manifest.json').read_text());rows=[];rng=random.Random(seed)
    kinds=['on-demand','pooling','pooling-compact'];rng.shuffle(kinds)
    for kind in kinds:
        eng=engine(kind)
        modules={r['file']:wt.Module(eng,(source/r['file']).read_bytes()) for r in manifest['rows']}
        for fixture in ('small','medium','large'):
            for job in ('work-only','grow-drop'):
                entries=[r for r in manifest['rows'] if r['fixture']==fixture and r['job']==job]
                base=next(r for r in entries if r['mode']=='source')
                for n in ([0,65536,1048576] if fixture=='large' else [0,65536]):
                    with wt.Store(eng) as store:
                        original=wt.Instance(store,modules[base['file']],[]).exports(store)
                        expected=original['__request'](store,n)
                    samples={r['mode']:[] for r in entries};repeats=20 if fixture=='large' else 100
                    for round in range(-3,15):
                        order=list(entries);rng.shuffle(order)
                        for row in order:
                            value=lib.measure(api,eng.ptr(),modules[row['file']].ptr(),repeats,n,row['mode']!='source',expected)
                            if value<=0:raise RuntimeError((kind,fixture,job,n,row['mode'],value))
                            if round>=0:samples[row['mode']].append(value)
                    for row in entries:
                        rows.append({'allocator':kind,'fixture':fixture,'job':job,'n':n,'mode':row['mode'],
                                     'repetitions':repeats,'samplesNs':samples[row['mode']],
                                     'medianNs':statistics.median(samples[row['mode']])})
        for mod in modules.values():mod.close()
        eng.close()
    return {'rows':rows,'platform':platform.platform(),'python':platform.python_version(),
            'wasmtime':importlib.metadata.version('wasmtime'),'seed':seed,
            'note':'Native C API loop; compiled modules cached. Store allocation, instance creation, one export lookup and deletion are timed in source. Reset and work are one Wasm wrapper call. Resident options have no effect on Windows.'}

def main(source,out):
    out.mkdir(parents=True,exist_ok=False)
    for name in ('pooling.py','native-loop.rs'):shutil.copy2(HERE/name,out/name)
    dll=out/'native-loop.dll'
    build=['rustc','--edition','2021','--crate-type','cdylib','-O',str(HERE/'native-loop.rs'),'-o',str(dll)]
    result=subprocess.run(build,capture_output=True,text=True,encoding='utf8',timeout=120)
    (out/'build.json').write_text(json.dumps({'command':build,'code':result.returncode,'stdout':result.stdout,'stderr':result.stderr},indent=2))
    if result.returncode:raise RuntimeError(result.stderr)
    raw=[]
    try:
        for i in range(5):
            cmd=[sys.executable,str(HERE/'pooling.py'),'--child',str(source.resolve()),str(dll.resolve()),str(20261024+i)]
            run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=180)
            raw.append({'command':cmd,'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
            (out/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf8')
            if run.returncode:raise RuntimeError(run.stderr)
            print(json.dumps({'process':i+1}),flush=True)
        runs=[json.loads(x['stdout']) for x in raw];summary=[]
        for row in runs[0]['rows']:
            keys=('allocator','fixture','job','n','mode');key=tuple(row[k] for k in keys)
            values=[next(r['medianNs'] for r in d['rows'] if tuple(r[k] for k in keys)==key) for d in runs]
            bases=[next(r['medianNs'] for r in d['rows'] if tuple(r[k] for k in keys)==(*key[:-1],'source')) for d in runs]
            ratios=[a/b for a,b in zip(values,bases)]
            summary.append({**dict(zip(keys,key)),'medianNs':statistics.median(values),'processMedians':values,
                            'pairedToFresh':statistics.median(ratios),'pairedQuartiles':statistics.quantiles(ratios,n=4,method='inclusive')})
        (out/'results.json').write_text(json.dumps({'rows':summary,'processes':5,'rounds':15,'warmup':3,
            'inputManifestHash':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest()},indent=2),encoding='utf8')
    finally:
        (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2),encoding='utf8')

if __name__=='__main__':
    if sys.argv[1]=='--child':print(json.dumps(child(Path(sys.argv[2]),Path(sys.argv[3]),int(sys.argv[4]))))
    else:
        a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
