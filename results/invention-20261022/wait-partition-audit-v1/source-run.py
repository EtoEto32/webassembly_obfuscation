import argparse,json,platform,shutil,subprocess,hashlib
from pathlib import Path
import prototype as p
import model

def save(f,v):Path(f).write_text(json.dumps(v,indent=2),encoding='utf8')

def run(output):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
    for profile in ('low','high','both','wide'):
        src=out/f'{profile}.plain.raw.wasm';p.compile(p.fixture(profile),src)
        for mode in ('plain','identity','auto'):
            raw=out/f'{profile}.{mode}.raw.wasm'
            stats=dict(codec='identity',bytes=src.stat().st_size,transform_ms=0) if mode=='plain' else p.transform(src,raw,mode)
            opt=out/f'{profile}.{mode}.O3.wasm';p.w.tool('wasm-opt',[raw,'--enable-threads','-O3','-o',opt])
            p.w.tool('wasm-validate',[opt,'--enable-threads'])
            for version,file in (('raw',raw),('O3',opt)):
                rows.append(dict(stats,profile=profile,mode=mode,version=version,file=file.name,bytes=file.stat().st_size))
    save(out/'manifest.json',rows);save(out/'model.json',model.check())
    for label,codec in (('plain','identity'),('compatible','low'),('bad','wide')):
        # prepare/commit split is deliberate scheduling instrumentation of the naive snapshot translation.
        p.compile('''(module (import "env" "memory" (memory 1 1 shared))
          (func (export "prepare") (result i32) (i32.atomic.load (i32.const 0)))
          (func (export "commit") (param i32) (result i32) (memory.atomic.wait32 (i32.const 0) (local.get 0) (i64.const -1)))
          (func (export "write") (param i64) (i64.atomic.store (i32.const 0) (call $wp_enc (local.get 0))))
          (func (export "notify") (result i32) (memory.atomic.notify (i32.const 0) (i32.const 1)))'''+p.codecs(codec)+')',out/f'witness.{label}.wasm')
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),processor=platform.processor(),wabt=p.w.tool('wat2wasm',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip()))
    for script in ('check.cjs','parallel.cjs','counterexample.cjs','performance.cjs'):
        r=subprocess.run(['node',str(Path(__file__).with_name(script)),str(out)],capture_output=True,text=True,timeout=240)
        (out/(script+'.stdout.txt')).write_text(r.stdout,encoding='utf8');(out/(script+'.stderr.txt')).write_text(r.stderr,encoding='utf8')
        if r.returncode:raise RuntimeError(script+': '+r.stderr)
        print(r.stdout.strip(),flush=True)
    for f in Path(__file__).parent.iterdir():
        if f.suffix in ('.py','.cjs'):shutil.copy2(f,out/('source-'+f.name))
    # Pin the transitive tool/parser dependency as well.
    shutil.copy2(p.w.__file__,out/'source-common.py')
    save(out/'pins.json',{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='pins.json'})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');run(ap.parse_args().output)
