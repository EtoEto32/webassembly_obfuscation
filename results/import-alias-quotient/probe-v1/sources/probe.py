import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess
import transform as t

HERE=Path(__file__).resolve().parent


def partitions(n):
    def walk(xs):
        if len(xs)==n:yield xs;return
        for i in range(max(xs)+2):yield from walk(xs+[i])
    yield from walk([0])


def fixture(n,kind):
    imports=' '.join('(import "env" "m%d" (memory 1 3))'%i for i in range(n))
    exports=' '.join('(export "m%d" (memory %d))'%(i,i) for i in range(n))
    # Each fixture uses the highest-index memory to exercise representative shifts.
    k=n-1
    body={
      'store_load':f'(i32.store 0 (local.get 0) (local.get 1)) (i32.load {k} (local.get 0))',
      'overlap_copy':f'(memory.copy {k} 0 (local.get 0) (local.get 1) (local.get 2)) (i32.load8_u {k} (local.get 0))',
      'fill_load':f'(memory.fill 0 (local.get 0) (local.get 1) (local.get 2)) (i32.load8_u {k} (local.get 0))',
      'grow_size':f'(drop (memory.grow 0 (local.get 0))) (memory.size {k})',
      'write_trap':f'(i32.store8 0 (i32.const 7) (local.get 1)) (i32.load {k} (local.get 0))',
      'branch':f'(if (i32.and (local.get 1) (i32.const 1)) (then (i32.store8 0 (local.get 0) (local.get 1))) (else (i32.store8 {k} (local.get 0) (local.get 2)))) (i32.load8_u {k} (local.get 0))',
      'data_init':f'(memory.init {k} 0 (local.get 0) (local.get 1) (local.get 2)) (i32.load8_u 0 (local.get 0))',
      'data_drop':f'(data.drop 0) (memory.init {k} 0 (local.get 0) (local.get 1) (local.get 2)) (i32.load8_u 0 (local.get 0))',
    }[kind]
    data='(data "abcdefghijklmnop")' if kind.startswith('data_') else ''
    # Multiple active segments deliberately overlap when their memories alias.
    active=' '.join('(data (memory %d) (i32.const 20) "\\%02x\\%02x")'%(i,65+i,81+i) for i in range(n))
    return f'(module {imports} (func (export "run") (param i32 i32 i32) (result i32) {body}) {exports} {data} {active})'


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('plan.md','probe.py','run.cjs','transform.py'):shutil.copy2(HERE/name,out/'sources'/name)
    records=[];rng=random.Random(2026102410)
    # Inputs exercise zero-length, overlap, page ends, wrap-sized indices, and grow limits.
    inputs=[[0,1,4],[1,0,8],[8,0,16],[0,8,16],[65535,255,1],[65536,1,0],[65533,19,4],[0xffffffff,0,0],[196607,33,1],[20,16,0]]
    inputs += [[rng.randrange(0,64),rng.randrange(0,32),rng.randrange(0,20)] for _ in range(10)]
    try:
        for n in (2,3,4):
          for kind in ('store_load','overlap_copy','fill_load','grow_size','write_trap','branch','data_init','data_drop'):
            folder=out/(str(n)+'-'+kind);folder.mkdir();wp=folder/'original.wat';src=folder/'original.wasm';wp.write_text(fixture(n,kind),encoding='utf8')
            t.w.tool('wat2wasm',[wp,'-o',src]);t.w.tool('wasm-validate',[src])
            t.w.tool('wasm-opt',[src,'--enable-multimemory','-O3','-o',folder/'original-O3.wasm'])
            if kind=='store_load':
                # Intentional invalid load motion across a possibly aliasing store.
                mutant=fixture(n,kind).replace('(result i32) '+f'(i32.store 0 (local.get 0) (local.get 1)) (i32.load {n-1} (local.get 0))',
                    '(result i32) (local i32) '+f'(local.set 3 (i32.load {n-1} (local.get 0))) (i32.store 0 (local.get 0) (local.get 1)) (local.get 3)')
                mp=folder/'mutant.wat';mp.write_text(mutant,encoding='utf8');t.w.tool('wat2wasm',[mp,'-o',folder/'mutant.wasm'])
            aliases=[]
            for i,p in enumerate(partitions(n)):
                dest=folder/('q'+str(i)+'.wasm');rep=t.quotient(src,dest,p)
                t.w.tool('wasm-opt',[dest,'--enable-multimemory','-O3','-o',folder/('q'+str(i)+'-O3.wasm')])
                aliases.append({'id':i,**rep})
            records.append({'folder':folder.name,'n':n,'kind':kind,'aliases':aliases})
        manifest={'seed':2026102410,'platform':platform.platform(),'python':platform.python_version(),'records':records,'inputs':inputs}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
        cmd=['node',str(HERE/'run.cjs'),str(out)];r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
