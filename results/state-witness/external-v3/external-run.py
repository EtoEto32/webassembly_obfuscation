"""Compare a pinned external transformer using a local host adapter."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BUILD=ROOT/'.tools/wasm-migrate-build'


def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];exe=BUILD/'target/release/wasm-migrate-probe.exe'
    cases=[('retained',False,'(data "X")',1),('dropped',True,'(data "X")',1),
           ('empty-dropped',True,'(data "")',0),('active',False,'(data (i32.const 16) "X")',1)]
    for name,drop,data,offset in cases:
        wat='''(module (memory (export "memory") 1 2) DATA
          (func (export "_start")
            (block (i32.store (i32.const 0) (i32.const 11)) DROP)
            (block (i32.store (i32.const 0) (i32.const 22)))
            (memory.init 0 (i32.const 0) (i32.const OFFSET) (i32.const 0))
            (i32.store (i32.const 0) (i32.add (i32.load (i32.const 0)) (i32.const 1))))
          (func (export "value") (result i32) (i32.load (i32.const 0))))'''.replace('DROP','data.drop 0' if drop else 'nop').replace('DATA',data).replace('OFFSET',str(offset))
        src=out/(name+'.wasm');k.p.compile_wat(wat,src)
        obs=out/(name+'-observed.wasm');meta=k.transform(src,obs,True)
        for kind,source in [('plain',src),('observed',obs)]:
            dest=out/(name+'-'+kind+'-migrate.wasm');cmd=[str(exe),str(source),str(dest)]
            r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=30)
            row={'name':name,'kind':kind,'source':source.name,'output':dest.name,'code':r.returncode,
                 'stdout':r.stdout,'stderr':r.stderr,'manifest':meta if kind=='observed' else None}
            if r.returncode==0:
                try:k.p.tool('wasm-validate',[dest]);row['status']='valid'
                except RuntimeError as e:row.update({'status':'invalid-output','validation':str(e)})
            else:row['status']='transform-failure'
            rows.append(row)
    for name in ('external-run.py','external-run.cjs','observer.cjs','prototype.py'):shutil.copy2(HERE/name,out/name)
    for name in ('Cargo.toml','Cargo.lock','provenance.json','driver-provenance.json','build-repair.json','build-repair-2.json','build.log'):
        shutil.copy2(BUILD/name,out/('upstream-'+name))
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'executableSha256':hashlib.sha256(exe.read_bytes()).hexdigest()},indent=2),encoding='utf8')
    cmd=['node',str(HERE/'external-run.cjs'),str(out.resolve())]
    r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'command':cmd,'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2))
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
