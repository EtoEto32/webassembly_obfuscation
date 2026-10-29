"""Compare before/after projections with real Jco nested-option lifting."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time
import fence

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(before,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('fence.py','fence-runtime.cjs','fence-shapes.py','fence-shapes.cjs','fence-shapes.wat','fence-shapes.wit','fence-shapes-policy.json','fence-shapes-plan.md'):
        shutil.copy2(HERE/name,out/'sources'/name)
    shutil.copy2(before,out/'sources/fence-before.py')
    spec=importlib.util.spec_from_file_location('old_fence',before);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    wit=(HERE/'fence-shapes.wit').read_text();policy=json.loads((HERE/'fence-shapes-policy.json').read_text())
    for name,implementation in [('before',old),('after',fence)]:
        (out/(name+'.cjs')).write_text(implementation.generate(implementation.Reader(wit).parse(),policy,'jco-host'),encoding='utf8')
    # Bindings alternate nullable and tagged options; exercise depths 1..4 separately.
    for depth in (1,2,3,4):
        nested='borrow<file>'
        for _ in range(depth):nested='option<'+nested+'>'
        text=wit.replace('option<option<borrow<file>>>',nested)
        p={**policy,'permissions':{**{k:v for k,v in policy['permissions'].items() if not k.startswith('value/nested')},'value/nested'+'/?'*depth:'write'}}
        (out/('depth-'+str(depth)+'.wit')).write_text(text,encoding='utf8')
        (out/('depth-'+str(depth)+'.cjs')).write_text(fence.generate(fence.Reader(text).parse(),p,'jco-host'),encoding='utf8')
    commands=[]
    def run(*args):
        start=time.perf_counter();r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120)
        commands.append({'argv':list(map(str,args)),'code':r.returncode,'ms':1000*(time.perf_counter()-start),'stdout':r.stdout,'stderr':r.stderr})
        (out/'commands.json').write_text(json.dumps(commands,indent=2),encoding='utf8');assert r.returncode==0,r.stderr+r.stdout
        return r.stdout
    try:
        for depth in (1,2,3,4):run('node',fence.JCO,'types',out/('depth-'+str(depth)+'.wit'),'-o',out/('types-'+str(depth)),'--name','unit','--instantiation','async','--quiet')
        run('node',fence.JCO,'parse',HERE/'fence-shapes.wat','-o',out/'raw.wasm')
        run('node',fence.JCO,'opt',out/'raw.wasm','-o',out/'optimized.wasm')
        for name in ('raw','optimized'):
            run('node',fence.JCO,'transpile',out/(name+'.wasm'),'-o',out/name,'--name','unit','--instantiation','async','--base64-cutoff','0','--no-wasi-shim','--quiet')
        print(run('node',HERE/'fence-shapes.cjs',out))
    finally:(out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('before',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();main(a.before.resolve(),a.output.resolve())
