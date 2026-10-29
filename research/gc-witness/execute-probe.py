"""Fuel- and memory-bounded execution of the previously generated local modules."""
import argparse,collections,json,subprocess,shutil
from pathlib import Path
from experiment import ROOT,HERE,CHECKER,wt,dump,digest
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];cfg=wt.Config();cfg.consume_fuel=True;engine=wt.Engine(cfg)
    for record in json.loads((source/'rows.json').read_text()):
        if record['status']!='ok':continue
        name=record['name'];seed=record['seed'];ref=source/(name+'.wasm');inp=source/('%s-%d.wasm'%(name,seed));dest=out/inp.name
        cp=subprocess.run([str(CHECKER),'instrument',str(ref),'0',str(inp),str(dest)],capture_output=True,text=True,timeout=8);cp.check_returncode();ins=json.loads(cp.stdout)
        row=dict(name=name,seed=seed,instrumentation=ins)
        if ins['status']!='instrumented':row['status']='instrumentation-rejected';rows.append(row);continue
        # The seed reference file contains only a type and an exported observe function.
        wat=(source/(name+'.wat')).read_text();types=wat[len('(module '):wat.index(' (func')]
        wrapper='(module '+types+' (import "target" "observe" (func $f (param (ref null $a)) (result i32))) (func (export "run") (result i32) (call $f (ref.null $a))))'
        store=wt.Store(engine);store.set_fuel(100000);store.set_limits(memory_size=16*1024*1024,table_elements=16384,instances=8,tables=8,memories=8)
        phase='compilation'
        try:
            module=wt.Module(engine,dest.read_bytes());phase='instantiation';inst=wt.Instance(store,module,[])
            linker=wt.Linker(engine);linker.define_instance(store,'target',inst);wrapped=linker.instantiate(store,wt.Module(engine,wt.wat2wasm(wrapper)))
            phase='execution'
            try:row['result']=wrapped.exports(store)['run'](store);row['status']='returned'
            except wt.Trap as e:row['status']='fuel' if 'fuel' in str(e) else 'trap';row['error']=str(e)
            row['constructed']=inst.exports(store)['__r_constructed'].value(store);row['accessed']=inst.exports(store)['__r_accessed'].value(store)
        except Exception as e:row['status']=phase+'-error';row['error']=str(e)
        rows.append(row)
    summary={name:dict(status=dict(collections.Counter(r['status'] for r in rows if r['name']==name)),successful_constructor_runs=sum(r.get('constructed',0)>0 for r in rows if r['name']==name),successful_access_runs=sum(r.get('accessed',0)>0 for r in rows if r['name']==name)) for name in sorted(set(r['name'] for r in rows))}
    dump(out/'rows.json',rows);dump(out/'summary.json',summary)
    for p in [HERE/'execute-probe.py',HERE/'checker/src/main.rs',HERE/'checker/src/instrument.rs',CHECKER]:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(summary,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.source,a.out)
