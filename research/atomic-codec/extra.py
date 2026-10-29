import json,subprocess,sys
from pathlib import Path
import prototype as p
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
src=out/'source.wasm'
p.compile('''(module (import "env" "memory" (memory 1 1 shared))
 (func (export "nested") (param i32 i32 i32) (result i32)
   (i32.atomic.rmw.add (local.get 0) (i32.add (i32.atomic.rmw.add (local.get 0) (local.get 1)) (local.get 2))))
 (func (export "address") (param i32 i32 i32) (result i32)
   (i32.atomic.rmw.add (i32.add (local.get 0) (i32.and (i32.atomic.rmw.add (i32.const 0) (i32.const 1)) (i32.const 0))) (local.get 1)))
 (func (export "prefix") (param i32 i32 i32) (result i32)
   (i32.atomic.store (i32.const 8) (local.get 1)) (i32.atomic.rmw.add (local.get 0) (local.get 2)))
 (func (export "success") (param i32 i32 i32) (result i32)
   (i32.atomic.store (local.get 0) (local.get 1)) (i32.atomic.rmw.cmpxchg (local.get 0) (local.get 1) (local.get 2))))''',src)
rows=[]
for mode in ['plain','native-neg','cas-neg','cas-affine','native-affine']:
    raw=out/(mode+'-raw.wasm');meta=p.transform(src,raw,mode)
    for opt in ('raw','O3'):
        f=raw if opt=='raw' else out/(mode+'-O3.wasm')
        if opt=='O3':p.q.tool('wasm-opt',[raw,'-O3','--enable-threads','-o',f]);p.q.w.tool('wasm-validate',[f,'--enable-threads'])
        rows.append(dict(**meta,opt=opt,file=f.name,sha256=p.q.digest(f)))
(out/'manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
subprocess.run(['node',str(Path(__file__).with_name('extra.cjs')),str(out)],check=True,timeout=60)
