"""Control-flow regressions and generated differential checks for effects.py."""
import argparse
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import effects

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('boundary',HERE/'boundary.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('effects.py','effects-audit.py','effects-audit.cjs'):
        shutil.copy2(HERE/name,out/'sources'/name)
    fixtures={
      'branch-skips-assignment':('ranges','(local.set 3 (i32.const 16)) (block (br_if 0 (local.get 2)) (local.set 3 (i32.const 24))) (i32.store8 (local.get 3) (local.get 1))'),
      'if-merge':('ranges','(if (local.get 2) (then (local.set 3 (i32.const 8))) (else (local.set 3 (i32.const 12)))) (i32.store8 (local.get 3) (local.get 1))'),
      'nested-if-branch':('ranges','(local.set 3 (i32.const 16)) (block (if (local.get 2) (then (local.set 3 (i32.const 20)) (br 1))) (local.set 3 (i32.const 24))) (i32.store8 (local.get 3) (local.get 1))'),
      'implicit-function-label':('ranges','(i32.store8 (i32.const 12) (local.get 1)) (br 0) (i32.store8 (i32.const 20) (local.get 1))'),
      'return-prefix':('ranges','(i32.store8 (i32.const 12) (local.get 1)) (return) (i32.store8 (i32.const 20) (local.get 1))'),
      'trap-prefix':('ranges','(i32.store8 (i32.const 12) (local.get 1)) (unreachable)'),
      'load-value':('ranges','(i32.store8 (i32.const 24) (i32.load8_u (local.get 0)))'),
      'load-address':('full','(i32.store8 (i32.load (i32.const 0)) (local.get 1))'),
      'store-evaluation-order':('ranges','(local.set 3 (i32.const 24)) (i32.store8 (local.get 3) (local.tee 3 (i32.const 12))) (i32.store8 (local.get 3) (local.get 1))'),
      'condition-tee':('ranges','(block (br_if 0 (local.tee 3 (i32.and (local.get 0) (i32.const 255)))) (local.set 3 (i32.const 16))) (i32.store8 (local.get 3) (local.get 1))'),
      'bulk-length-tee':('ranges','(memory.fill (i32.const 100) (local.get 1) (local.tee 3 (i32.and (local.get 2) (i32.const 63)))) (i32.store8 (local.get 3) (local.get 1))'),
      'unknown-import':('full','(call $mutate)'),
      'value-call':('full','(i32.store8 (i32.const 24) (call $value))'),
      'loop':('full','(loop (i32.store8 (i32.const 16) (local.get 1)))'),
      'grow':('full','(drop (memory.grow (i32.const 0)))'),
      'wrap-vs-offset':('ranges','(i32.store8 offset=4 (i32.add (local.get 0) (i32.const -1)) (local.get 1))'),
    }
    rng=random.Random(20261024)
    for i in range(48):
        a,c,d=[rng.randrange(8,256) for _ in range(3)]
        fixtures['generated-%02d'%i]=('ranges',f'''(local.set 3 (i32.const {a}))
          (block (br_if 0 (i32.and (local.get 2) (i32.const 1)))
            (local.set 3 (i32.const {c})))
          (if (i32.and (local.get 2) (i32.const 2))
            (then (i32.store8 (local.get 3) (local.get 1)))
            (else (local.set 3 (i32.const {d}))))
          (i32.store8 (local.get 3) (i32.add (i32.load8_u (i32.and (local.get 0) (i32.const 255))) (local.get 1)))''')
    manifest=[]
    for name,(expected,body) in fixtures.items():
        wat=f'''(module (import "host" "mutate" (func $mutate))
          (memory (export "memory") 1 1)
          (func $value (result i32) (i32.store8 (i32.const 48) (i32.const 255)) (i32.const 9))
          (func (export "callback") (param i32 i32 i32) (local i32) {body}))'''
        source=out/(name+'.wat');source.write_text(wat,encoding='utf8')
        raw=out/(name+'-raw.wasm');b.p.w.tool('wat2wasm',[source,'-o',raw])
        opt=out/(name+'-O3.wasm');b.p.w.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',opt])
        for binary in (raw,opt):
            b.p.w.tool('wasm-validate',[binary])
            folded=b.p.w.tool('wasm2wat',[binary,'--fold-exprs'])
            binary.with_suffix('.wat').write_text(folded,encoding='utf8')
            certificate=effects.summary(b.p.w.parse(folded))
            # Optimizers can remove unsupported effects, so only the raw
            # classification is fixed. Both versions must pass dynamic checks.
            if binary==raw: assert certificate['kind']==expected,(name,certificate)
            manifest.append({'file':binary.name,'sha256':b.p.digest(binary),'summary':certificate})
    rejected=[]
    for name,memory in [('shared','1 1 shared'),('memory64','i64 1 1')]:
        source=out/(name+'.wat');source.write_text('(module (memory (export "memory") '+memory+') (func (export "callback") (param i32 i32 i32)))',encoding='utf8')
        binary=out/(name+'.wasm');b.p.w.tool('wat2wasm',[source,'--enable-all','-o',binary])
        b.p.w.tool('wasm-validate',[binary,'--enable-all'])
        result=effects.summary(b.p.w.parse(b.p.w.tool('wasm2wat',[binary,'--enable-all','--fold-exprs'])))
        assert result['kind']=='reject';rejected.append({'file':binary.name,'summary':result})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    (out/'rejected.json').write_text(json.dumps(rejected,indent=2),encoding='utf8')
    r=subprocess.run(['node',str(HERE/'effects-audit.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):b.p.digest(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    if r.returncode: raise RuntimeError(r.stderr)
    print(r.stdout)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path)
    main(ap.parse_args().output.resolve())
