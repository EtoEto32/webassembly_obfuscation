import argparse,json,subprocess
from pathlib import Path
import prototype as q
from run import kernels,HERE
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);base=kernels()['random16'];models={'one':[[0,0,1]],'two':[[0,1,0],[1,0,1]],'random16':base};q.save(out/'models.json',models);rows=[]
    cases=[('one',2,1),('one',32,512),('two',2,1),('two',32,512),('random16',32,512),('random16',3,65)]
    for i,(k,g,d) in enumerate(cases):
        src=out/f'case{i}-source.wasm';q.p.compile(q.packed(models[k]),src);raw=out/f'case{i}-raw.wasm';info=q.transform(src,raw,'groups',g,d,19)
        for opt in ('raw','O3'):
            f=raw if opt=='raw' else out/f'case{i}-O3.wasm'
            if opt=='O3':q.tool('wasm-opt',[raw,*q.FEATURES,'-O3','-o',f])
            r=out/(f.stem+'-lower.wasm');a=q.lower(f,r);a.pop('output');rows.append(dict(info,kernel=k,opt=opt,source=src.name,file=f.name,recovered=r.name,analysis=a,sha256=q.digest(f),recovered_sha256=q.digest(r),bytes=f.stat().st_size))
    q.save(out/'manifest.json',rows);subprocess.run(['node',str(HERE/'check.cjs'),str(out)],check=True,timeout=120)
    rejects=[];normal=q.packed(models['two'])
    wrong=[normal.replace('(module','(module (memory 1)',1),normal.replace('(module','(module (import "x" "f" (func)))',1),normal.replace('"run"','"different"'),'(module (func (export "run") (param f64) (result f64) (local.get 0)))']
    # The import fixture must keep the module body inside its original parentheses.
    wrong[1]=normal.replace('(module','(module (import "x" "f" (func))',1)
    for i,wat in enumerate(wrong):
        f=out/f'reject-source{i}.wasm';q.p.compile(wat,f)
        try:q.transform(f,out/f'unexpected-source{i}.wasm');raise AssertionError('Unsupported source accepted')
        except ValueError as e:rejects.append(dict(action='transform',file=f.name,status='unsupported',reason=str(e)))
    invalid_lower=['(module (type $t (struct (field i32))) (global eqref (struct.new $t (i32.const 0))) (func (export "run") (result i32) (i32.const 0)))','(module (type $t (struct)) (global $a eqref (struct.new_default $t)) (func (export "run") (result i32) (ref.eq (global.get $a) (global.get $a))))']
    for i,wat in enumerate(invalid_lower):
        f=out/f'reject-lower{i}.wasm';w=f.with_suffix('.wat');w.write_text(wat,encoding='utf-8');q.tool('wasm-as',[w,*q.FEATURES,'-o',f])
        try:q.lower(f,out/f'unexpected-lower{i}.wasm');raise AssertionError('Unsupported lowering accepted')
        except ValueError as e:rejects.append(dict(action='lower',file=f.name,status='unsupported',reason=str(e)))
    q.save(out/'refusals.json',rejects);c=json.loads((out/'checks.json').read_text());q.save(out/'summary.json',dict(targets=12,constant_targets=4,nonconstant_targets=8,wasm_calls=c['wasm_calls'],mismatches=c['mismatches'],refusals=len(rejects)));print(json.dumps(json.loads((out/'summary.json').read_text())))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
