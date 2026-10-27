"""Measure static/entered/attempted/completed GC operations in real wasm-smith outputs."""
import argparse,collections,hashlib,importlib.util,json,platform,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.append(str(ROOT/'research/gc-witness'))
from experiment import wt,dump,digest
spec=importlib.util.spec_from_file_location('input_probe',ROOT/'research/gc-witness/smith-input-experiment.py');inputs=importlib.util.module_from_spec(spec);spec.loader.exec_module(inputs)
DRIVER=ROOT/'.tools/gc-execution-gap-target/release/gc-execution-gap-driver.exe'
INSTRUMENT=ROOT/'.tools/gc-execution-gap-instrument-target/release/gc-execution-gap-instrument.exe'
SOURCE=ROOT/'results/gc-witness/smith-v2'

def command(args):
    p=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=20)
    if p.returncode:raise RuntimeError(p.stderr)
    return json.loads(p.stdout)

def run(engine,module,caller,provider,metadata,counted):
    s=wt.Store(engine);s.set_fuel(100000);s.set_limits(memory_size=16*1024*1024,table_elements=16384,instances=8,tables=8,memories=8);r={};phase='instantiation'
    try:
        target=wt.Instance(s,module,[]);link=wt.Linker(engine);link.define_instance(s,'target',target)
        if provider is not None:link.define_instance(s,'input',wt.Instance(s,provider,[]))
        c=link.instantiate(s,caller);phase='execution';t=time.perf_counter_ns()
        try:r['result']=c.exports(s)['run'](s);r['status']='returned'
        except wt.Trap as e:r['status']='fuel' if 'fuel' in str(e) else 'trap';r['error']=str(e);r['cause']=str(e).split('Caused by:')[-1].strip()
        r['execution_ms']=(time.perf_counter_ns()-t)/1e6;r['fuel_remaining']=s.get_fuel()
        if counted:
            values=[target.exports(s)['__gap_%d'%i].value(s) for i in range(metadata['counter_count'])];n=len(metadata['functions']);r['function_entries']=values[:n];r['site_counts']=[dict(attempted=values[n+2*i],completed=values[n+2*i+1]) for i in range(len(metadata['sites']))]
    except Exception as e:r['status']=phase+'-error';r['error']=str(e)
    return r

def categories(meta,r):
    result=collections.Counter();target=collections.Counter()
    for site,c in zip(meta['sites'],r['site_counts']):
        if c['completed']:state='completed'
        elif c['attempted']:state='attempted-not-completed'
        elif r['function_entries'][site['function']]:state='function-entered-site-not-reached'
        else:state='function-not-entered'
        result[state]+=1
        if site['target'] and site['kind'] in ('StructGet','StructGetS','StructGetU','StructSet','ArrayGet','ArrayGetS','ArrayGetU','ArraySet'):target[state]+=1
    return dict(all_gc=dict(result),target_access=dict(target))

def calibrate(out,engine,call,providers):
    definition='(type $a (array (mut (ref null $a))))';rows=[];errors=[]
    bodies={
        'length':'(array.len (local.get 0))',
        'get':'(drop (array.get $a (local.get 0) (i32.const 0))) (i32.const 1)',
        'not-reached':'(if (i32.const 0) (then (drop (array.get $a (local.get 0) (i32.const 0))))) (i32.const 1)',
        'private':'(i32.const 1)',
        'packed':'(drop (struct.get_u $p 0 (struct.new $p (i32.const -1)))) (i32.const 1)',
    }
    shape=SOURCE/'nullable-array-shape.wasm'
    for name,body in bodies.items():
        extra='(func (param (ref null $a)) (drop (array.get $a (local.get 0) (i32.const 0))))' if name=='private' else ''
        wat='(module '+definition+' (type $p (struct (field i8))) (func (export "observe") (param (ref null $a)) (result i32) '+body+') '+extra+')';raw=out/(name+'.wasm');raw.write_bytes(wt.wat2wasm(wat));raw.with_suffix('.wat').write_text(wat)
        dest=out/(name+'-counted.wasm');meta=command([INSTRUMENT,shape,raw,dest,'count']);assert meta['status']=='instrumented';mod=wt.Module(engine,dest.read_bytes());plain=wt.Module(engine,raw.read_bytes())
        for v in ['null','depth1']:
            r=run(engine,mod,call[v],providers.get(v),meta,True);p=run(engine,plain,call[v],providers.get(v),meta,False);cat=categories(meta,r)
            expected=('trap' if v=='null' and name in ('length','get') else 'returned')
            expected_cat={'attempted-not-completed':1} if expected=='trap' else {'function-entered-site-not-reached':1} if name=='not-reached' else {'function-not-entered':1} if name=='private' else {'completed':2 if name=='packed' else 1}
            if r['status']!=expected or p['status']!=expected or cat['all_gc']!=expected_cat:errors.append(dict(name=name,variant=v,r=r,cat=cat,expected=expected_cat))
            rows.append(dict(name=name,variant=v,counted=r,plain=p,categories=cat,metadata=meta))
    dump(out/'rows.json',rows);dump(out/'validation.json',dict(cases=len(rows),errors=errors));assert not errors

def main(out,seeds):
    out.mkdir(parents=True,exist_ok=False);cfg=wt.Config();cfg.consume_fuel=True;engine=wt.Engine(cfg);rows=[];meta_rows=[];errors=[];byte_replays=0;error_replays=0
    originals={(r['name'],r['seed']):r for r in json.loads((SOURCE/'rows.json').read_text()) if r['mode']=='stock'}
    for name in ['cycle-array','nullable-array','scalar-array','cycle-struct']:
        shape=SOURCE/(name+'-shape.wasm');call,providers,_=inputs.callers(shape,out,name,engine)
        if name=='nullable-array':
            cal=out/'calibration';cal.mkdir();calibrate(cal,engine,call,providers)
        variants=['null'] if name=='cycle-struct' else ['null','depth1']
        for seed in range(seeds):
            for profile in ['default','no-traps']:
                key='%s-%d-%s'%(name,seed,profile);raw=out/(key+'.wasm');gen=command([DRIVER,shape,SOURCE/(name+'-%d.seed'%seed),raw,profile]);m=dict(name=name,seed=seed,profile=profile,generation=gen)
                if profile=='default':
                    old=originals[name,seed]['generation']
                    if gen['status']=='generated' and old['status']=='generated':
                        byte_replays+=1
                        if raw.read_bytes()!=(SOURCE/('%s-%d-stock.wasm'%(name,seed))).read_bytes():errors.append(dict(kind='default-binary',key=key))
                    elif gen['status']=='error' and old['status']=='error':
                        error_replays+=1
                        if gen['reason']!=old['reason']:errors.append(dict(kind='default-generation-error',key=key))
                    else:errors.append(dict(kind='default-outcome',key=key))
                if gen['status']!='generated':meta_rows.append(m);continue
                paths={};metas={};modules={}
                for mode in ['plain','count']:
                    paths[mode]=out/(key+'-'+mode+'.wasm');metas[mode]=command([INSTRUMENT,shape,raw,paths[mode],mode]);assert metas[mode]['status']=='instrumented';modules[mode]=wt.Module(engine,paths[mode].read_bytes())
                m.update(metadata=metas['count'],raw_sha256=digest(raw),count_sha256=digest(paths['count']),plain_sha256=digest(paths['plain']));meta_rows.append(m)
                for variant in variants:
                    plain=run(engine,modules['plain'],call[variant],providers.get(variant),metas['plain'],False);counted=run(engine,modules['count'],call[variant],providers.get(variant),metas['count'],True)
                    if plain['status'].endswith('error') or counted['status'].endswith('error'):errors.append(dict(kind='runtime-process',key=key,variant=variant,plain=plain,counted=counted));continue
                    rs=dict(name=name,seed=seed,profile=profile,variant=variant,plain=plain,counted=counted,categories=categories(metas['count'],counted),status_equal=plain['status']==counted['status'],result_equal=plain.get('result')==counted.get('result'));rows.append(rs)
                if seed%16==0:print(json.dumps(dict(progress=key,rows=len(rows))),flush=True)
    summary={}
    for profile in ['default','no-traps']:
        summary[profile]={}
        for variant in ['null','depth1']:
            rs=[r for r in rows if r['profile']==profile and r['variant']==variant];total=collections.Counter();target=collections.Counter()
            for r in rs:total.update(r['categories']['all_gc']);target.update(r['categories']['target_access'])
            summary[profile][variant]=dict(runs=len(rs),plain_status=dict(collections.Counter(r['plain']['status'] for r in rs)),counted_status=dict(collections.Counter(r['counted']['status'] for r in rs)),site_run_all_gc=dict(total),site_run_target_access=dict(target),modules_with_successful_target_access=sum(r['categories']['target_access'].get('completed',0)>0 for r in rs),status_discrepancies=sum(not r['status_equal'] for r in rs),result_discrepancies=sum(not r['result_equal'] for r in rs))
    validation=dict(default_byte_replays=byte_replays,default_error_replays=error_replays,generated=sum(m['generation']['status']=='generated' for m in meta_rows),attempts=len(meta_rows),paired_runs=len(rows),engine_calls=2*len(rows),errors=errors)
    dump(out/'modules.json',meta_rows);dump(out/'rows.json',rows);dump(out/'summary.json',summary);dump(out/'validation.json',validation);dump(out/'settings.json',dict(source=str(SOURCE),source_manifest_sha256=digest(SOURCE/'manifest.json'),fuel=100000,engine='Wasmtime 50.0.1',seeds=seeds,array_length_mask=31,profiles=['default','no-traps'],variants=['null','depth1'],platform=platform.platform(),python=sys.version))
    src=out/'source';src.mkdir()
    for path in [Path(__file__),HERE/'plan.md',HERE/'driver/src/main.rs',HERE/'driver/Cargo.lock',HERE/'instrument/src/main.rs',HERE/'instrument/Cargo.lock',DRIVER,INSTRUMENT]:
        prefix=path.parent.parent.name+'-' if path.suffix=='.rs' else path.parent.name+'-' if path.name=='Cargo.lock' else '';shutil.copy2(path,src/(prefix+path.name))
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(dict(validation=validation,summary=summary),indent=2));assert not errors

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--seeds',type=int,default=64);a=ap.parse_args();main(a.out,a.seeds)
