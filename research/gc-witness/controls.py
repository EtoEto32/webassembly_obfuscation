"""Negative controls and execution-counter calibration on actual Wasm."""
import argparse,json,subprocess,shutil
from pathlib import Path
from experiment import wt,ROOT,HERE,CHECKER,dump,digest
from witness import read,Unsupported
def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];engine=wt.Engine();errors=[]
    arr='(rec (type $a (array (ref $a))))'
    struct='(rec (type $a (struct (field (ref $a)))))'
    tests=[
      ('empty-array-get',arr,'(array.get $a (array.new_fixed $a 0) (i32.const 0))','drop i32.const 1','trap',[1,0]),
      ('successful-get',arr,'(array.get $a (array.new_fixed $a 1 (array.new_fixed $a 0)) (i32.const 0))','ref.is_null i32.eqz','ok',[2,1]),
      ('null-seed',struct,'(struct.new $a (ref.as_non_null (ref.null $a)))','drop i32.const 1','trap',[0,0]),
      ('post-construction-trap',arr,'(array.new_fixed $a 0)','drop unreachable','trap',[1,0]),
      ('function-is-not-its-result','(rec (type $a (func (result (ref $s)))) (type $s (struct (field (ref $s))))) (func $f (type $a) unreachable) (elem declare func $f)','(call_ref $a (ref.func $f))','drop i32.const 1','trap',[0,0]),
    ]
    for name,types,expr,suffix,expected,counts in tests:
        wat='(module '+types+' (func (export "run") (result i32) '+expr+' '+suffix+'))';p=out/(name+'.wasm');p.write_bytes(wt.wat2wasm(wat));(out/(name+'.wat')).write_text(wat)
        dest=out/(name+'-counted.wasm');cp=subprocess.run([str(CHECKER),'instrument',str(p),'0',str(p),str(dest)],capture_output=True,text=True,timeout=10);cp.check_returncode();instr=json.loads(cp.stdout)
        row=dict(name=name,instrumentation=instr,expected=expected,expected_counts=counts)
        if instr['status']!='instrumented':errors.append(row);rows.append(row);continue
        for variant,path in [('raw',p),('counted',dest)]:
            store=wt.Store(engine);instance=wt.Instance(store,wt.Module(engine,path.read_bytes()),[])
            try:r=instance.exports(store)['run'](store);obs=dict(status='ok',result=r)
            except wt.Trap as e:obs=dict(status='trap',error=str(e))
            if variant=='counted':obs['counts']=[instance.exports(store)[x].value(store) for x in ['__r_constructed','__r_accessed']]
            row[variant]=obs
            if obs['status']!=expected or obs.get('counts',counts)!=counts:errors.append(dict(name=name,variant=variant,observed=obs))
        rows.append(row)
    rejected=[
      ('array-default-nonnull','(module '+arr+' (func (export "run") (result i32) (array.new_default $a (i32.const 0)) drop i32.const 1))','validation'),
      ('inheritance','(module (type (sub (struct))))','non-final'),
      ('abstract-nonnull','(module (type (struct (field (ref eq)))))','non-null abstract'),
    ]
    for name,wat,reason in rejected:
        p=out/(name+'.wasm');p.write_bytes(wt.wat2wasm(wat));(out/(name+'.wat')).write_text(wat)
        try:read(p);row=dict(name=name,status='unexpected-accept');errors.append(row)
        except Unsupported as e:row=dict(name=name,status='rejected',reason=str(e));assert reason in str(e)
        rows.append(row)
    dump(out/'rows.json',rows);dump(out/'summary.json',dict(executed_pairs=len(tests),rejection_controls=len(rejected),errors=errors))
    for p in [HERE/'controls.py',HERE/'checker/src/instrument.rs',CHECKER]:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(dict(controls=len(rows),errors=errors)));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
