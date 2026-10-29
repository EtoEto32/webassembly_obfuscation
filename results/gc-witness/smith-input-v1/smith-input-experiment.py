"""Feed fixed-depth typed values to the SAME generated modules, fresh per call."""
import argparse,collections,json,shutil,time,subprocess
from pathlib import Path
from experiment import ROOT,HERE,wt,dump,digest,CHECKER
from witness import read,generate,type_text

VARIANTS=['null','empty','depth1','depth2','depth4']

def callers(shape,out,name,engine):
    model=read(shape);types=type_text(model);mods={};providers={};meta=[]
    for variant in VARIANTS:
        if name=='cycle-struct' and variant!='null':continue
        make='';expr='(ref.null $t0)'
        if variant!='null':
            depth=0 if variant=='empty' else int(variant[5:]);start=time.perf_counter_ns()
            if name=='scalar-array':
                wat='(module '+types+' (func (export "run") (result (ref $t0)) (array.new $t0 (i32.const 0) (i32.const '+str(depth)+'))))'
                nodes=1
            else:
                g=generate(model,0,['e']*depth,return_root=True);wat=g['wat'];nodes=g['nodes']
            elapsed=(time.perf_counter_ns()-start)/1e6;path=out/(name+'-'+variant+'-provider.wasm');path.write_bytes(wt.wat2wasm(wat));path.with_suffix('.wat').write_text(wat);providers[variant]=wt.Module(engine,path.read_bytes())
            meta.append(dict(name=name,variant=variant,plan_ms=elapsed,nodes=nodes,bytes=path.stat().st_size))
            make='(import "input" "run" (func $make (result (ref $t0))))';expr='(call $make)'
        wat='(module '+types+' (import "target" "observe" (func $f (param (ref null $t0)) (result i32))) '+make+' (func (export "run") (result i32) (call $f '+expr+')))'
        path=out/(name+'-'+variant+'-caller.wasm');path.write_bytes(wt.wat2wasm(wat));path.with_suffix('.wat').write_text(wat);mods[variant]=wt.Module(engine,path.read_bytes())
    return mods,providers,meta

def run(engine,module,caller,provider):
    store=wt.Store(engine);store.set_fuel(100000);store.set_limits(memory_size=16*1024*1024,table_elements=16384,instances=8,tables=8,memories=8);r={};phase='instantiation'
    try:
        inst=wt.Instance(store,module,[]);link=wt.Linker(engine);link.define_instance(store,'target',inst)
        if provider is not None:link.define_instance(store,'input',wt.Instance(store,provider,[]))
        c=link.instantiate(store,caller);phase='execution';t=time.perf_counter_ns()
        try:r['result']=c.exports(store)['run'](store);r['status']='returned'
        except wt.Trap as e:r['status']='fuel' if 'fuel' in str(e) else 'trap';r['error']=str(e)
        r['execution_ms']=(time.perf_counter_ns()-t)/1e6;r['fuel_remaining']=store.get_fuel();r['constructed']=inst.exports(store)['__r_constructed'].value(store);r['accessed']=inst.exports(store)['__r_accessed'].value(store)
    except Exception as e:r['status']=phase+'-error';r['error']=str(e)
    return r

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);cfg=wt.Config();cfg.consume_fuel=True;engine=wt.Engine(cfg);rows=[];errors=[];meta=[];cal=[];replayed=0
    originals=json.loads((source/'rows.json').read_text())
    for name in ['cycle-array','nullable-array','scalar-array','cycle-struct']:
        shape=source/(name+'-shape.wasm');call,prov,m=callers(shape,out,name,engine);meta+=m
        for old in originals:
            if old['name']!=name or old.get('generation',{}).get('status')!='generated':continue
            path=source/('%s-%d-%s-counted.wasm'%(name,old['seed'],old['mode']));module=wt.Module(engine,path.read_bytes())
            for variant in call:
                r=dict(name=name,seed=old['seed'],mode=old['mode'],variant=variant,source_sha256=digest(path),**run(engine,module,call[variant],prov.get(variant)))
                if variant=='null':
                    replayed+=1
                    if any(r.get(k)!=old.get(k) for k in ['status','constructed','accessed']):errors.append(dict(kind='null-replay',name=name,seed=old['seed'],mode=old['mode']))
                if r['status'].endswith('-error'):errors.append(dict(kind='execution-error',row=r))
                rows.append(r)
        if name=='cycle-struct':continue
        # Known simple consumers calibrate input depth and counters independently.
        types=type_text(read(shape))
        for depth in [1,2,4]:
            expr='(local.get 0)'
            if name=='scalar-array':expr='(array.get $t0 '+expr+' (i32.const '+str(depth-1)+'))'
            else:
                for _ in range(depth):expr='(array.get $t0 '+expr+' (i32.const 0))'
            wat='(module '+types+' (func (export "observe") (param (ref null $t0)) (result i32) (drop '+expr+') (i32.const 1)))';raw=out/(name+'-consumer%d.wasm'%depth);raw.write_bytes(wt.wat2wasm(wat));raw.with_suffix('.wat').write_text(wat);counted=out/(name+'-consumer%d-counted.wasm'%depth)
            cp=subprocess.run([str(CHECKER),'instrument',str(shape),'0',str(raw),str(counted),'--bound-arrays'],capture_output=True,text=True,timeout=10);cp.check_returncode();assert json.loads(cp.stdout)['status']=='instrumented';mod=wt.Module(engine,counted.read_bytes())
            for variant in call:
                input_depth=0 if variant in ('null','empty') else int(variant[5:]);r=dict(name=name,depth=depth,variant=variant,expected_status='returned' if input_depth>=depth else 'trap',**run(engine,mod,call[variant],prov.get(variant)))
                expected_access=(1 if input_depth>=depth else 0) if name=='scalar-array' else min(input_depth,depth)
                if r['status']!=r['expected_status'] or r.get('accessed')!=expected_access:errors.append(dict(kind='calibration',row=r,expected_access=expected_access))
                cal.append(r)
    summary={}
    for name in ['cycle-array','nullable-array','scalar-array','cycle-struct']:
        summary[name]={}
        for mode in ['stock','zero']:
            rs=[r for r in rows if r['name']==name and r['mode']==mode];byvariant={}
            for v in VARIANTS:
                vr=[r for r in rs if r['variant']==v]
                if vr:byvariant[v]=dict(runs=len(vr),statuses=dict(collections.Counter(r['status'] for r in vr)),successful_access_runs=sum(r.get('accessed',0)>0 for r in vr),total_accesses=sum(r.get('accessed',0) for r in vr))
            empty={r['seed'] for r in rs if r['variant']=='empty' and r.get('accessed',0)>0};deep={r['seed'] for r in rs if r['variant'].startswith('depth') and r.get('accessed',0)>0}
            summary[name][mode]=dict(variants=byvariant,deep_access_seeds=sorted(deep),new_access_seeds_vs_empty=sorted(deep-empty))
    dump(out/'rows.json',rows);dump(out/'summary.json',summary);dump(out/'providers.json',meta);dump(out/'calibration.json',cal);dump(out/'validation.json',dict(null_replays=replayed,calibration_cases=len(cal),calls=len(rows),errors=errors));dump(out/'settings.json',dict(source=str(source.resolve()),source_manifest_sha256=digest(source/'manifest.json'),fuel=100000,variants=VARIANTS,engine='Wasmtime 50.0.1',fresh_instance_per_call=True,target_only_counters=True))
    for p in [Path(__file__),HERE/'witness.py',HERE/'smith-input-plan.md',CHECKER]:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(dict(validation=json.loads((out/'validation.json').read_text()),summary=summary),indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.source,a.out)
