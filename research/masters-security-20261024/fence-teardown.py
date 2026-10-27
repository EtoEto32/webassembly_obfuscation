"""Build a trap-after-prepare component and test host-owned teardown."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import fence

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(source,out):
    hashes=json.loads((source/'sha256.json').read_text())
    for relative,digest in hashes.items():assert sha(source/relative)==digest
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('fence-teardown.py','fence-teardown.cjs','fence-teardown-plan.md','fence-runtime.cjs','fence.py'):
        shutil.copy2(HERE/name,out/'sources'/name)
    shutil.copy2(source/'project.cjs',out/'project.cjs')
    base=(source/'sources/component-fence.wat').read_text()
    old='(func (export "request") (param $mode'
    assert base.count(old)==1
    wat=base.replace(old,'(func $request (export "request") (param $mode')
    marker='  (core instance $i\n'
    assert wat.count(marker)==1
    pos=wat.index(marker)
    # Insert the extra function before the core module closes.
    close=wat.rfind('  )',0,pos)
    wat=wat[:close]+'''    (func (export "request-then-trap") (param i32 i32)
      (drop (call $request (local.get 0) (local.get 1))) unreachable)
'''+wat[close:]
    assert wat.rstrip().endswith(')')
    wat=wat.rstrip()[:-1]+'''
  (func (export "request-then-trap") (param "mode" u32) (param "count" u32)
    (canon lift (core func $g "request-then-trap"))))
'''
    (out/'component.wat').write_text(wat,encoding='utf8')
    (out/'component-source.json').write_text(json.dumps({'path':str(source),'hashes':hashes},indent=2),encoding='utf8')
    commands=[]
    def run(*args):
        start=time.perf_counter();r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120)
        commands.append({'argv':list(map(str,args)),'code':r.returncode,'ms':1000*(time.perf_counter()-start),'stdout':r.stdout,'stderr':r.stderr})
        (out/'commands.json').write_text(json.dumps(commands,indent=2),encoding='utf8')
        assert r.returncode==0,r.stderr+r.stdout
        return r.stdout
    try:
        run('node',fence.JCO,'parse',out/'component.wat','-o',out/'raw.wasm')
        run('node',fence.JCO,'opt',out/'raw.wasm','-o',out/'optimized.wasm')
        for name in ('raw','optimized'):
            run('node',fence.JCO,'transpile',out/(name+'.wasm'),'-o',out/name,'--name','unit','--instantiation','async','--base64-cutoff','0','--no-wasi-shim','--quiet')
        print(run('node',HERE/'fence-teardown.cjs',out))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
