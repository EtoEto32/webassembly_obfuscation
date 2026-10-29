"""Boundary cases for the conservative write-footprint selector."""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('qc',HERE/'queue-free.py');q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('footprint-audit.py','footprint-audit.cjs','queue-free.py'):shutil.copy2(HERE/name,out/'sources'/name)
    rows=[]
    try:
        for base,offset in itertools.product((0,1,2,3,4,65528,65532,65535,-1,-2147483648),(0,1,4,4294967295)):
            name=f'constant-{base}-{offset}';body=f'(i32.store offset={offset} align=1 (i32.const {base}) (i32.const 305419896))'
            address=(base&0xffffffff)+offset
            rows.append({'name':name,'body':body,'addresses':[address],'dynamic':False})
        rows.extend([
            {'name':'two-stores','body':'(i32.store (i32.const 0) (i32.const 305419896)) (i32.store (i32.const 4) (i32.const 305419896))','addresses':[0,4],'dynamic':False},
            {'name':'dynamic','body':'(i32.store (local.get 0) (i32.const 305419896))','addresses':[0],'dynamic':True},
            {'name':'wrapped-expression','body':'(i32.store (i32.add (i32.const -1) (i32.const 1)) (i32.const 305419896))','addresses':[0],'dynamic':True}])
        for row in rows:
            wat=f'(module (import "env" "memory" (memory 1 4 shared)) (func (export "run") (param i32) {row.pop("body")}))'
            (out/(row['name']+'.wat')).write_text(wat,encoding='utf8');binary=out/(row['name']+'.wasm')
            q.w.tool('wat2wasm',[out/(row['name']+'.wat'),'--enable-threads','-o',binary]);cert=q.check(binary)
            row['certificate']=cert
            if row['dynamic']:assert cert['stableOffset'] is None
            else:assert cert['stableOffset'] is not None
        (out/'cases.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
        cmd=['node',str(HERE/'footprint-audit.cjs'),str(out)];p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2),encoding='utf8')
        if p.returncode:raise RuntimeError(p.stderr)
        print(p.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
