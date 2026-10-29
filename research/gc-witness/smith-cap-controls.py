"""Calibrate the explicitly non-equivalent length cap used by smith trials."""
import argparse,json,subprocess,shutil
from pathlib import Path
from experiment import wt,CHECKER,dump,digest

def main(out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();rows=[];errors=[]
    for instruction in ['array.new','array.new_default']:
        for n in [0,1,31,32,63,255,-1,-2147483648]:
            name=instruction+'-'+str(n);init='(i32.const 7)' if instruction=='array.new' else ''
            wat='(module (type $a (array (mut i32))) (func (export "run") (result i32) (array.len ('+instruction+' $a '+init+' (i32.const '+str(n)+')))))'
            raw=out/(name+'.wasm');raw.write_bytes(wt.wat2wasm(wat));(out/(name+'.wat')).write_text(wat)
            counted=out/(name+'-counted.wasm');p=subprocess.run([str(CHECKER),'instrument',str(raw),'0',str(raw),str(counted),'--bound-arrays'],capture_output=True,text=True,timeout=10);p.check_returncode();ins=json.loads(p.stdout);assert ins['status']=='instrumented'
            store=wt.Store(engine);inst=wt.Instance(store,wt.Module(engine,counted.read_bytes()),[]);value=inst.exports(store)['run'](store);counts=[inst.exports(store)[x].value(store) for x in ['__r_constructed','__r_accessed']]
            row=dict(instruction=instruction,input_length=n,expected_length=n&31,actual_length=value,counts=counts,instrumentation=ins)
            if value!=n&31 or counts!=[1,0]:errors.append(row)
            # Only run raw cases with small allocations; never allocate the huge lengths.
            if 0<=n<=255:
                s=wt.Store(engine);i=wt.Instance(s,wt.Module(engine,raw.read_bytes()),[]);row['raw_length']=i.exports(s)['run'](s)
                if row['raw_length']!=n:errors.append(row)
            rows.append(row)
    dump(out/'rows.json',rows);dump(out/'summary.json',dict(cases=len(rows),raw_small_cases=sum('raw_length' in r for r in rows),errors=errors))
    for p in [Path(__file__),CHECKER]:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print((out/'summary.json').read_text());assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
