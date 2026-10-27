"""Build a real imported-resource component and exercise generated host fences."""
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
def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    names=['fence.py','fence.wit','fence-policy.json','component-fence.py','component-fence.cjs','component-fence.wat','component-fence-plan.md']
    for name in names:shutil.copy2(HERE/name,out/'sources'/name)
    model=fence.Reader((HERE/'fence.wit').read_text()).parse()
    policy=json.loads((HERE/'fence-policy.json').read_text())
    (out/'project.cjs').write_text(fence.generate(model,policy,'jco-host'),encoding='utf8')
    commands=[]
    def run(*args):
        start=time.perf_counter();r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120)
        commands.append({'argv':list(map(str,args)),'returncode':r.returncode,'ms':(time.perf_counter()-start)*1000,'stdout':r.stdout,'stderr':r.stderr})
        (out/'commands.json').write_text(json.dumps(commands,indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr+r.stdout)
        return r.stdout
    run('node',fence.JCO,'parse',HERE/'component-fence.wat','-o',out/'raw.wasm')
    run('node',fence.JCO,'opt',out/'raw.wasm','-o',out/'optimized.wasm')
    rows=[]
    for name in ('raw','optimized'):
        run('node',fence.JCO,'transpile',out/(name+'.wasm'),'-o',out/name,'--name','unit','--instantiation','async','--base64-cutoff','0','--no-wasi-shim','--quiet')
        wit=run('node',fence.JCO,'wit',out/(name+'.wasm'))
        (out/(name+'.wit')).write_text(wit,encoding='utf8')
        rows.append({'name':name,'componentBytes':(out/(name+'.wasm')).stat().st_size,'sha256':sha(out/(name+'.wasm'))})
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'generatedBytes':(out/'project.cjs').stat().st_size,'binding':'Jco 1.27.0 imported resource; option none is undefined'},indent=2),encoding='utf8')
    try:print(run('node',HERE/'component-fence.cjs',out))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path)
    main(ap.parse_args().output.resolve())
