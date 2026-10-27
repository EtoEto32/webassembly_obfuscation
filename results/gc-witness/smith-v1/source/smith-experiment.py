"""Stock vs minimal zero-operand patch, with equal bounded guest execution."""
import argparse,collections,json,random,shutil,subprocess,time,statistics
from pathlib import Path
from experiment import ROOT,HERE,CHECKER,wt,dump,digest
def command(args,timeout=15):
    t=time.perf_counter_ns()
    try:
        p=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout)
        return dict(code=p.returncode,stdout=p.stdout,stderr=p.stderr,ms=(time.perf_counter_ns()-t)/1e6)
    except subprocess.TimeoutExpired:return dict(code=None,status='timeout',ms=(time.perf_counter_ns()-t)/1e6)
def main(out,seeds):
    out.mkdir(parents=True,exist_ok=False);rows=[];cfg=wt.Config();cfg.consume_fuel=True;engine=wt.Engine(cfg)
    types={
        'cycle-array':'(rec (type $a (array (mut (ref $a)))))',
        'nullable-array':'(rec (type $a (array (mut (ref null $a)))))',
        'scalar-array':'(type $a (array (mut i32)))',
        'cycle-struct':'(rec (type $a (struct (field (ref $a)))))'
    }
    for name,definition in types.items():
        wat='(module '+definition+' (func (export "observe") (param (ref null $a)) (result i32) (i32.const 1)))';shape=out/(name+'-shape.wasm');shape.write_bytes(wt.wat2wasm(wat));(out/(name+'-shape.wat')).write_text(wat)
        wrapper='(module '+definition+' (import "target" "observe" (func $f (param (ref null $a)) (result i32))) (func (export "run") (result i32) (call $f (ref.null $a))))'
        wrapper=wt.Module(engine,wt.wat2wasm(wrapper))
        for seed in range(seeds):
            rng=random.Random(seed);inp=out/(name+'-%d.seed'%seed);inp.write_bytes(bytes(rng.getrandbits(8) for _ in range(8192)))
            for mode in ['stock','zero']:
                driver=ROOT/('.tools/gc-witness-smith-'+mode+'.exe');dest=out/('%s-%d-%s.wasm'%(name,seed,mode));counted=out/('%s-%d-%s-counted.wasm'%(name,seed,mode));r=dict(name=name,seed=seed,mode=mode)
                gen=command([driver,shape,inp,dest]);r['generation_process']=gen
                if gen['code']!=0:r['status']='generation-timeout' if gen['code'] is None else 'generation-process-error';rows.append(r);continue
                g=json.loads(gen['stdout']);r['generation']=g
                if g['status']!='generated':r['status']='generation-error';rows.append(r);continue
                cp=command([CHECKER,'instrument',shape,'0',dest,counted,'--bound-arrays']);r['instrumentation_process']=cp
                if cp['code']!=0:r['status']='instrumentation-process-error';rows.append(r);continue
                ins=json.loads(cp['stdout']);r['instrumentation']=ins
                if ins['status']!='instrumented':r['status']='instrumentation-rejected';rows.append(r);continue
                store=wt.Store(engine);store.set_fuel(100000);store.set_limits(memory_size=16*1024*1024,table_elements=16384,instances=8,tables=8,memories=8);phase='compilation'
                try:
                    module=wt.Module(engine,counted.read_bytes());phase='instantiation';instance=wt.Instance(store,module,[]);linker=wt.Linker(engine);linker.define_instance(store,'target',instance);caller=linker.instantiate(store,wrapper);phase='execution';t=time.perf_counter_ns()
                    try:r['result']=caller.exports(store)['run'](store);r['status']='returned'
                    except wt.Trap as e:r['status']='fuel' if 'fuel' in str(e) else 'trap';r['error']=str(e)
                    r['execution_ms']=(time.perf_counter_ns()-t)/1e6;r['fuel_remaining']=store.get_fuel();r['constructed']=instance.exports(store)['__r_constructed'].value(store);r['accessed']=instance.exports(store)['__r_accessed'].value(store)
                except Exception as e:r['status']=phase+'-error';r['error']=str(e)
                rows.append(r)
    summary={}
    for name in types:
        summary[name]={}
        for mode in ['stock','zero']:
            rs=[r for r in rows if r['name']==name and r['mode']==mode];generated=[r for r in rs if r.get('generation',{}).get('status')=='generated']
            summary[name][mode]=dict(status=dict(collections.Counter(r['status'] for r in rs)),generated=len(generated),static_constructor_runs=sum(r.get('instrumentation',{}).get('sites',[0])[0]>0 for r in rs),successful_constructor_runs=sum(r.get('constructed',0)>0 for r in rs),successful_access_runs=sum(r.get('accessed',0)>0 for r in rs),median_generation_ms=statistics.median(r['generation']['generation_ms'] for r in generated) if generated else None,total_bytes=sum(r['generation']['bytes'] for r in generated))
    dump(out/'rows.json',rows);dump(out/'summary.json',summary);dump(out/'settings.json',dict(seeds=seeds,seed_bytes=8192,seed_origin='Python random.Random(integer)',fuel=100000,array_length_mask=31,entry='observe(null)',wasm_smith='0.262.0',driver_source=str(HERE/'smith-driver/src/main.rs')))
    src=out/'source';src.mkdir()
    for p in [HERE/'smith-experiment.py',HERE/'prepare-smith.py',HERE/'smith-zero-seed.patch',HERE/'smith-driver/Cargo.toml',HERE/'smith-driver/Cargo.lock',HERE/'smith-driver/src/main.rs',HERE/'checker/src/instrument.rs',CHECKER,ROOT/'.tools/gc-witness-smith-stock.exe',ROOT/'.tools/gc-witness-smith-zero.exe',ROOT/'.tools/gc-witness-smith-patched/patch-provenance.json',ROOT/'.tools/gc-witness-smith-upstream/provenance.json']:shutil.copy2(p,src/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(summary,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--seeds',type=int,default=64);a=ap.parse_args();main(a.out,a.seeds)
