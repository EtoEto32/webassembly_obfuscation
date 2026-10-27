import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import probe as p
import transform as t

HERE=Path(__file__).resolve().parent


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('subset-audit.py','subset-audit.cjs','guard.cjs','transform.py','probe.py'):shutil.copy2(HERE/name,out/'sources'/name)
    rows=[]
    try:
        # Valid core modules but unsupported by this deliberately narrow analysis.
        base='(module (import "env" "mark" (func (param i32 i32))) {extra} (func (export "run") (param i32 i32) (result i32) {body}))'
        cases={'loop':('', '(loop) (local.get 0)'),
          'memory':('(memory 1)','(i32.load (i32.const 0))'),
          'division':('','(i32.div_u (local.get 0) (local.get 1))'),
          'variable-marker':('','(call 0 (i32.const 0) (local.get 0)) (local.get 1)'),
          'reserved-marker':('','(call 0 (i32.const -2147483648) (i32.const 0)) (local.get 1)'),
          'early-return':('','(return (local.get 0))'),
          'global':('(global i32 (i32.const 0))','(global.get 0)'),
          'extra-function':('(func (result i32) (i32.const 0))','(call 1)')}
        for name,(extra,body) in cases.items():
            src=out/(name+'.wasm');wat=src.with_suffix('.wat');wat.write_text(base.format(extra=extra,body=body),encoding='utf8');t.w.tool('wat2wasm',[wat,'-o',src]);t.w.tool('wasm-validate',[src])
            try:t.analyze(src,True)
            except ValueError as e:rows.append({'name':name,'status':'unsupported','reason':str(e)})
            else:raise AssertionError('unexpected acceptance '+name)
        m=p.fixture('early-split')
        def rewrite(x):
            if not isinstance(x,list):return
            if x[0]=='call':x[2]=['i32.const','2147483647'];x[3]=['i32.const','-2147483648' if x[3][1]=='0' else '-1']
            for v in x[1:]:rewrite(v)
        rewrite(m);src=out/'signed.wasm';src.with_suffix('.wat').write_text(t.w.emit(m),encoding='utf8');t.w.tool('wat2wasm',[src.with_suffix('.wat'),'-o',src]);t.transform(src,out/'signed-target.wasm',True)
        (out/'subset.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
        cmd=['node',str(HERE/'subset-audit.cjs'),str(out)];r=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
