import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('helper',ROOT/'research/connectivity-elimination/prototype.py');w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for p in HERE.iterdir():
        if p.suffix in ('.cjs','.py','.md'):shutil.copy2(p,out/'sources'/p.name)
    shutil.copy2(ROOT/'research/connectivity-elimination/prototype.py',out/'sources/wat-helper.py')
    try:
        wat='''(module (import "env" "a" (memory 1 4 shared)) (import "env" "b" (memory 1 4 shared))
          (func (export "run") (param i32) (result i32)
            (i32.store 0 (i32.const 8) (local.get 0))
            (i32.load 1 (i32.const 8))))'''
        (out/'pair.wat').write_text(wat,encoding='utf8');w.tool('wat2wasm',[out/'pair.wat','--enable-threads','--enable-multi-memory','-o',out/'pair.wasm']);w.tool('wasm-validate',[out/'pair.wasm','--enable-threads','--enable-multi-memory'])
        cmd=['node',str(HERE/'probe.cjs'),str(out)];p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2),encoding='utf8')
        if p.returncode:raise RuntimeError(p.stderr)
        print(p.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);main(p.parse_args().output.resolve())
