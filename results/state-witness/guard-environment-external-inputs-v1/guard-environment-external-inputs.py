"""Finite public-memory inputs; no private diagnostic exports."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    exes={'migrate':ROOT/'.tools/wasm-migrate-build/target/release/wasm-migrate-target.exe','weave':ROOT/'.tools/weave-build/target/release/weave-probe.exe'}
    for name,n,repair,zero in [('one',1,False,False),('four',4,False,False),('repair',4,True,False),('zero',4,False,True)]:
        folder=out/name;folder.mkdir();payload=''.join('\\%02x'%((i+1)*17) for i in range(n))
        prefix=' '.join(f'(i32.store8 (i32.const {7+i}) (i32.const {(i+1)*17}))' for i in range(n)) if repair else ''
        # This repair control is executed by the engines, outside the bulk-only analyser.
        def text(cut):return f'''(module (memory (export "memory") 1 1) (data "{payload}") (data "B") (data (i32.const 7) "{payload}")
          (func (export "retire") (data.drop 0) {'(loop (br_if 0 (i32.const 0)))' if cut else ''})
          (func (export "mask") {prefix} (memory.init 0 (i32.const 7) (i32.const 0) (i32.const {0 if zero else n}))
            (memory.init 1 (i32.const 0) (i32.const 2) (i32.const 1))))'''
        original=folder/'original.wasm';cut=folder/'cut.wasm';k.p.compile_wat(text(False),original);k.p.compile_wat(text(True),cut);variants=[]
        for backend,exe in exes.items():
            dest=folder/(backend+'.wasm');cmd=[str(exe),str(cut),str(dest)]+(['0'] if backend=='migrate' else [])
            try:
                run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=30);row={'backend':backend,'binary':dest.relative_to(out).as_posix(),'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr}
                if run.returncode:row['status']='transform-failure'
                else:
                    try:k.p.tool('wasm-validate',[dest]);row['status']='valid'
                    except RuntimeError as err:row.update(status='invalid-output',reason=str(err))
            except subprocess.TimeoutExpired:row={'backend':backend,'status':'transform-timeout'}
            variants.append(row)
        rows.append({'name':name,'length':n,'repair':repair,'zeroLength':zero,'original':original.relative_to(out).as_posix(),'cut':cut.relative_to(out).as_posix(),'variants':variants})
    shutil.copy2(ROOT/'.tools/weave-build/js/weave.mjs',out/'weave.mjs')
    for name in ('guard-environment-external-inputs.py','guard-environment-external-plan.md','prototype.py'):shutil.copy2(HERE/name,out/name)
    result={'rows':rows,'executableSha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in exes.values()}}
    (out/'manifest.json').write_text(json.dumps(result,indent=2));(out/'sha256.json').write_text(json.dumps({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2));print(json.dumps({'inputs':len(rows),'validTransforms':sum(v['status']=='valid' for r in rows for v in r['variants'])}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
