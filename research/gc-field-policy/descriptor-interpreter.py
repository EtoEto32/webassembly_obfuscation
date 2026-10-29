import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
from workload import ROOT,HERE,command


def main(out):
    out.mkdir(parents=True,exist_ok=False);s=runpy.run_path(str(HERE/'descriptor-screen.py'))
    chunks=[s['LIB'],'(register "lib")']
    for name,(body,expected) in s['CASES'].items():
        chunks.append(f';; {name}\n(module {s["TYPES"]} {s["IMPORTS"]} (func (export "run") (result i32) {body}))')
        chunks.append(f'(assert_return (invoke "run") (i32.const {expected["value"]}))' if expected['type']=='return' else '(assert_trap (invoke "run") "cast failure")')
    file=out/'screen.wast';file.write_text('\n'.join(chunks))
    c=command([ROOT/'.tools/binaryen-version_133/bin/wasm-shell.exe',file]);(out/'command.json').write_text(json.dumps(c,indent=2));assert c['code']==0,c
    (out/'summary.json').write_text(json.dumps(dict(interpreter='Binaryen 133 wasm-shell',assertions=4,engineNode='unsupported encoding',expected={k:v[1] for k,v in s['CASES'].items()}),indent=2))
    sources=out/'sources';sources.mkdir()
    for p in (HERE/'descriptor-interpreter.py',HERE/'descriptor-screen.py',HERE/'next-direction-screen.md'):shutil.copyfile(p,sources/p.name)
    (out/'hashes.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2))
    print(json.dumps(dict(interpreter='Binaryen 133',assertions=4,status='passed')))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
