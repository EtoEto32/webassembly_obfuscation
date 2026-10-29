import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import probe
import transform as t

HERE=Path(__file__).resolve().parent


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for n in ('release.py','release.cjs','release-plan.md','probe.py','transform.py'):
        shutil.copy2(HERE/n,out/'sources'/n)
    records=[]
    try:
        tree=probe.module('swap');tree[1]=['type',['func',['param','i32','i32']]]
        def markers(x):
            if not isinstance(x,list):return
            if x and x[0]=='call':x.append(['i32.shr_u',['local.get','2'],['i32.const','28']])
            else:
                for v in x:markers(v)
        markers(tree)
        tree[-2][-1]=['i32.shr_u',['local.get','2'],['i32.const','24']]
        wp=out/'original.wat';src=out/'original.wasm';wp.write_text(t.w.emit(tree),encoding='utf8');t.w.tool('wat2wasm',[wp,'-o',src])
        for name,flags in [('O3',['-O3']),('O3-flat',['-O3','--flatten'])]:
            dest=out/(name+'.wasm');start=time.perf_counter();t.w.tool('wasm-opt',[src,*flags,'-o',dest]);elapsed=time.perf_counter()-start
            t.w.tool('wasm-validate',[dest]);wat=t.w.tool('wasm2wat',[dest,'--fold-exprs']);dest.with_suffix('.wat').write_text(wat,encoding='utf8')
            r={'name':name,'normalizationSeconds':elapsed,'bytes':dest.stat().st_size,'ifs':wat.count('(if')}
            try:
                modes={mode:t.transform(dest,out/(name+'-'+mode+'.wasm'),mode,True) for mode in t.MODES}
                source_tree=t.w.parse(wat)
                independent=[probe.oracle(source_tree,[secret,0]) for secret in (0,1)]
                r.update(status='accepted',modes=modes,independentCost=independent)
            except ValueError as e:r.update(status='unsupported',reason=str(e))
            records.append(r)
        (out/'manifest.json').write_text(json.dumps({'records':records},indent=2),encoding='utf8')
        cmd=['node',str(HERE/'release.cjs'),str(out)];r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
