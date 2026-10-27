import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('qcheck',HERE/'queue-free.py');q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)

BODY='''(block (loop
  (br_if 1 (i32.eqz (local.get 0)))
  (drop (i32.atomic.rmw.add (i32.const 0) (i32.const 1)))
  (local.set 0 (i32.sub (local.get 0) (i32.const 1)))
  (br 0)))'''
def module(body,extra='',imp=''):
    return f'(module (import "env" "memory" (memory 1 4 shared)) {imp} (func (export "run") (param i32) {body}) {extra})'


def main(out):
    out.mkdir(parents=True,exist_ok=False); (out/'sources').mkdir()
    for f in ('concurrent.py','concurrent.cjs','concurrent-plan.md','queue-free.py','partition-concurrent.cjs'):
        shutil.copy2(HERE/f,out/'sources'/f)
    shutil.copy2(ROOT/'research/connectivity-elimination/prototype.py',out/'sources/wat-helper.py')
    rows=[]
    try:
        cases=[('writer',module(BODY),True),
               ('atomic-store',module('(i32.atomic.store (i32.const 0) (local.get 0))'),True),
               ('ordinary-store',module('(i32.store (i32.const 0) (local.get 0))'),True),
               ('atomic-load',module('(drop (i32.atomic.load (i32.const 0)))'),True),
               ('wait32',module('(drop (memory.atomic.wait32 (i32.const 0) (i32.const 0) (i64.const 0)))'),False),
               ('wait64',module('(drop (memory.atomic.wait64 (i32.const 0) (i64.const 0) (i64.const 0)))'),False),
               ('notify',module('(drop (memory.atomic.notify (i32.const 0) (i32.const 1)))'),False),
               ('dead-notify',module('(if (i32.const 0) (then (drop (memory.atomic.notify (i32.const 0) (i32.const 1)))))'),False),
               ('host-import',module(BODY,imp='(import "env" "callback" (func))'),False),
               ('memory-export',module(BODY,extra='(export "memory" (memory 0))'),False)]
        for name,wat,want in cases:
            src=out/(name+'.wat');binary=out/(name+'.wasm');src.write_text(wat,encoding='utf8')
            q.w.tool('wat2wasm',[src,'--enable-threads','-o',binary]);q.w.tool('wasm-validate',[binary,'--enable-threads'])
            try: certificate=q.check(binary); accepted=True; reason=None
            except ValueError as e: certificate=None; accepted=False; reason=str(e)
            assert accepted==want,(name,reason)
            rows.append({'name':name,'validWasm':True,'expected':want,'accepted':accepted,'reason':reason})
            if certificate:(out/(name+'.json')).write_text(json.dumps(certificate,indent=2),encoding='utf8')
        (out/'checker-results.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
        cmd=['node',str(HERE/'concurrent.cjs'),str(out)]; p=subprocess.run(cmd,text=True,capture_output=True,timeout=120)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2),encoding='utf8')
        if p.returncode: raise RuntimeError(p.stderr)
        print(p.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
