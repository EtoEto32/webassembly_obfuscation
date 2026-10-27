import argparse,importlib.util,json,shutil,subprocess
from pathlib import Path
from experiment import ROOT,HERE,SM,wt,dump,sha
spec=importlib.util.spec_from_file_location('caller_experiment',HERE/'caller-experiment.py');ce=importlib.util.module_from_spec(spec);spec.loader.exec_module(ce)

def fixtures():
    return [
      ('i64','(module (func (export "id") (param i64) (result i64) local.get 0))',{'null':{'type-error':1},'typed':{'returned':1}},None),
      ('numbers','(module (func (export "sum") (param i32 f32 f64) (result i32) (i32.add (local.get 0) (i32.add (i32.trunc_f32_s (local.get 1)) (i32.trunc_f64_s (local.get 2))))))',{'null':{'returned':1},'typed':{'returned':1}},None),
      ('nonnull','(module (type $t (struct)) (func (export "ref") (param (ref $t)) (result i32) i32.const 1))',{'null':{'type-error':1},'typed':{'type-error':1}},None),
      ('v128','(module (func (export "vec") (param v128) (result i32) i32.const 1))',{'null':{'type-error':1},'typed':{'type-error':1}},None),
      ('alias-exports','(module (func (export "a") (export "b") (param i64) (result i64) local.get 0))',{'null':{'type-error':2},'typed':{'returned':2}},None),
      ('imported-export','(module (import "fuzzing-support" "log-i64" (func $log (param i64))) (export "alias" (func $log)))',{'null':{'type-error':1},'typed':{'returned':1}},None),
      ('reentry','(module (import "fuzzing-support" "call-export" (func $call (param i32 i32))) (func (export "child") (param i64) (result i64) local.get 0) (func (export "outer") (call $call (i32.const 0) (i32.const 0))))',{'null':{'type-error':3},'typed':{'returned':3}},None),
      ('trap','(module (func (export "trap") unreachable))',{'null':{'trap':1},'typed':{'trap':1}},None),
      ('same-pair','(module (type $t (struct)) (global $g (ref $t) (struct.new $t)) (func (export "pair") (result eqref eqref) global.get $g global.get $g))',{'null':{'returned':1},'typed':{'returned':1}},[0,0]),
      ('different-pair','(module (type $t (struct)) (func (export "pair") (result eqref eqref) struct.new $t struct.new $t))',{'null':{'returned':1},'typed':{'returned':1}},[0,1]),
    ]

def main(out):
    out.mkdir(parents=True,exist_ok=False);shells=ce.make_shells(out);rows=[];errors=[]
    for name,wat,status,trace in fixtures():
      wasm=out/(name+'.wasm');wasm.write_bytes(wt.wat2wasm(wat));wasm.with_suffix('.wat').write_text(wat);api=ce.extract(wasm)
      for (caller,observer),shell in shells.items():
        for en,exe in [('node','node'),('spidermonkey',str(SM))]:
          p=ce.run([exe,shell,wasm],3);prefix='%s-%s-%s-%s'%(name,caller,observer,en);stdout=p.pop('stdout');stderr=p.pop('stderr');(out/(prefix+'.stdout')).write_text(stdout,encoding='utf8');(out/(prefix+'.stderr')).write_text(stderr,encoding='utf8')
          line=next((s for s in stdout.splitlines() if s.startswith('[caller-study] ')),None);study=json.loads(line[15:]) if line else None
          expected_trace=trace if observer=='multi' and trace is not None else []
          got={}
          if study:
            for c in study['calls']:got[c['status']]=got.get(c['status'],0)+1
          good=study is not None and got==status[caller] and [x['id'] for x in study['trace']]==expected_trace and all(c['known'] for c in study['calls'])
          row=dict(name=name,caller=caller,observer=observer,engine=en,passed=good,call_status=got,expected_status=status[caller],expected_trace=expected_trace,study=study,**p);rows.append(row)
          if not good:errors.append(row)
    # Invalid bytes and the extractor size limit must be reported as rejection.
    rejections=[]
    for name,data in [('invalid',b'notwasm'),('oversize',b'\0'*1048577)]:
      path=out/(name+'.bin');path.write_bytes(data);p=subprocess.run([str(ce.INTERFACE),str(path)],capture_output=True,text=True,timeout=10);r=json.loads(p.stdout);rejections.append(dict(name=name,**r))
      if r['status']!='rejected':errors.append(dict(kind='rejection',name=name))
    report=dict(fixtures=10,processes=len(rows),calls=sum(len(r['study']['calls']) for r in rows if r['study']),passed=sum(r['passed'] for r in rows),rejections=rejections,errors=errors)
    dump(out/'rows.json',rows);dump(out/'report.json',report);dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()]);print(json.dumps(report,indent=2));assert not errors

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out.resolve())
