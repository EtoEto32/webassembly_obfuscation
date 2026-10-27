"""Compare original/continuous/restored executions using the public Weave adapter."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def main(out,build):
    out.mkdir(parents=True,exist_ok=False);rows=[];exe=build/'target/release/weave-probe.exe'
    cases=[('retained',False,'(data "X")',1),('dropped',True,'(data "X")',1),
           ('empty-dropped',True,'(data "")',0),('active',False,'(data (i32.const 16) "X")',1)]
    for name,drop,data,offset in cases:
        wat='''(module (memory (export "memory") 1 2) DATA
          (func (export "_start") (local i32)
            (block (i32.store (i32.const 0) (i32.const 11)) DROP)
            (loop (local.set 0 (i32.add (local.get 0) (i32.const 1)))
              (br_if 0 (i32.lt_u (local.get 0) (i32.const 3))))
            (block (i32.store (i32.const 0) (i32.const 22)))
            (memory.init 0 (i32.const 0) (i32.const OFFSET) (i32.const 0))
            (i32.store (i32.const 0) (i32.add (i32.load (i32.const 0)) (i32.const 1))))
          (func (export "value") (result i32) (i32.load (i32.const 0))))'''.replace('DROP','data.drop 0' if drop else 'nop').replace('DATA',data).replace('OFFSET',str(offset))
        src=out/(name+'.wasm');k.p.compile_wat(wat,src)
        obs=out/(name+'-observed.wasm');k.transform(src,obs,True)
        for kind,source in [('plain',src),('observed',obs)]:
            dest=out/(name+'-'+kind+'-woven.wasm')
            r=subprocess.run([str(exe),str(source),str(dest)],capture_output=True,text=True,timeout=30)
            row={'name':name,'kind':kind,'source':source.name,'output':dest.name,'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
            if r.returncode==0:
                try:k.p.tool('wasm-validate',[dest]);row['status']='valid'
                except RuntimeError as e:row.update({'status':'invalid-output','validation':str(e)})
            else:row['status']='transform-failure'
            rows.append(row)
    for name in ('weave-run.py','weave-run.mjs','observer.cjs','prototype.py'):shutil.copy2(HERE/name,out/name)
    shutil.copy2(build/'js/weave.mjs',out/'weave.mjs')
    for name in ('Cargo.toml','Cargo.lock','provenance.json','driver-provenance.json','build.log'):
        shutil.copy2(build/name,out/('upstream-'+name))
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'executableHash':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2))
    cmd=['node',str(out/'weave-run.mjs'),str(out.resolve())];r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
    (out/'node-log.json').write_text(json.dumps({'command':cmd,'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2))
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);a.add_argument('--build',type=Path,default=ROOT/'.tools/weave-build')
    v=a.parse_args();main(v.out,v.build)
