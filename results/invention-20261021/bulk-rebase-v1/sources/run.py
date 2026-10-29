import json,platform,subprocess,sys
from pathlib import Path
import prototype as p

def source(pages):
    return f'''(module (memory {pages} {pages})
      (global (mut i32) (i32.const 0))
      (func (param i32 i32 i32) (memory.copy (local.get 0) (local.get 1) (local.get 2)))
      (func (param i32) (result i32) (i32.load8_u (local.get 0)))
      (func (param i32 i32) (i32.store8 (local.get 0) (local.get 1)))
      (func (param i32) (local i32)
        (block (loop (br_if 1 (i32.ge_u (local.get 1) (i32.const {pages*65536})))
        (local.set 0 (i32.add (i32.mul (local.get 0) (i32.const 1664525)) (i32.const 1013904223)))
        (i32.store8 (local.get 1) (i32.shr_u (local.get 0) (i32.const 24)))
        (local.set 1 (i32.add (local.get 1) (i32.const 1))) (br 0))))
      (func (param i32 i32 i32)
        (if (i32.eqz (local.get 1)) (then (return)))
        (memory.copy (local.get 0) (i32.add (local.get 0) (i32.const 1)) (i32.sub (local.get 1) (i32.const 1)))
        (i32.store8 (i32.add (local.get 0) (i32.sub (local.get 1) (i32.const 1))) (local.get 2)))
      (func (param i32 i32 i32 i32)
        (i32.store8 (i32.const 0) (local.get 3))
        (memory.copy (local.get 0) (local.get 1) (local.get 2)))
      (func (param i32) (result i32) (i32.load8_s (local.get 0)))
      (func (param i32 i32) (result i32)
        (global.set 0 (i32.add (i32.mul (global.get 0) (i32.const 5)) (local.get 1))) (local.get 0))
      (func (param i32 i32 i32)
        (memory.copy (call 7 (local.get 0) (i32.const 1)) (call 7 (local.get 1) (i32.const 2)) (call 7 (local.get 2) (i32.const 3))))
      (export "copy" (func 0)) (export "read" (func 1)) (export "write" (func 2)) (export "fill" (func 3))
      (export "splice" (func 4)) (export "markcopy" (func 5)) (export "signed" (func 6)) (export "ordered" (func 8)) (export "trace" (global 0))
      (data (i32.const 3) "abcdefghijklmnop") (data (i32.const 9) "UVWXYZ")
      (data (i32.const {pages*65536-2}) "\\fe\\ff"))'''

out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);q=p.q;rows=[]
env=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require("os").cpus()[0].model}))'],text=True))
q.save(out/'environment.json',dict(python=platform.python_version(),os=platform.platform(),wabt=q.w.tool('wat2wasm',['--version']).strip(),binaryen=q.tool('wasm-opt',['--version']).strip(),**env))
for pages in (1,2):
    src=out/f'p{pages}-source.wasm';q.compile(source(pages),src)
    for mode in p.MODES:
        for seed in ((0,) if mode=='plain' else (7,29)):
            f=out/f'p{pages}-{mode}-s{seed}-raw.wasm';info=p.transform(src,f,mode,seed)
            for opt in ('raw','O3'):
                target=f if opt=='raw' else f.with_name(f.name.replace('-raw','-O3'))
                if opt=='O3':q.tool('wasm-opt',[f,'--enable-simd','--enable-bulk-memory','-O3','-o',target])
                obs=out/(target.stem+'-observe.wasm');m=q.read(target);m.append(['export','"memory"',['memory','0']]);q.compile(q.w.emit(m),obs)
                rows.append(dict(info,pages=pages,opt=opt,file=target.name,observed=obs.name,source=src.name,bytes=target.stat().st_size,sha256=q.digest(target)))
q.save(out/'manifest.json',rows)
subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=180)
print(json.dumps(dict(targets=len(rows))))
