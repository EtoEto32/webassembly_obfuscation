import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import probe
import transform as t

HERE=Path(__file__).resolve().parent


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for n in ('audit.py','audit.cjs','audit-plan.md','probe.py','transform.py'):
        shutil.copy2(HERE/n,out/'sources'/n)
    rng=random.Random(2026102407);records=[]
    try:
        for case in range(24):
            k=case%4+1;arms=[]
            for arm in range(2):
                counts=[rng.randrange(0,10) for _ in range(k+1)]
                arms.append(probe.blocks(counts))
            # Two nested choices with the same common event word.
            inner=['if',['i32.and',['local.get','0'],['i32.const','2']],['then',*arms[0]],['else',*arms[1]]]
            tree=probe.module('swap');f=tree[-2]
            f[-2]=['if',['i32.and',['local.get','0'],['i32.const','1']],['then',inner],['else',*probe.blocks([rng.randrange(0,10) for _ in range(k+1)])]]
            folder=out/str(case);folder.mkdir();wp=folder/'original.wat';src=folder/'original.wasm'
            wp.write_text(t.w.emit(tree),encoding='utf8');t.w.tool('wat2wasm',[wp,'-o',src])
            report=t.transform(src,folder/'frontier.wasm','frontier')
            t.w.tool('wasm-opt',[folder/'frontier.wasm','-O3','-o',folder/'frontier-O3.wasm'])
            t.w.tool('wasm-validate',[folder/'frontier-O3.wasm'])
            samples=[{'args':[secret,payload],'expected':probe.oracle(tree,[secret,payload])} for secret in range(4) for payload in (0,1,0x80000000,0xffffffff,rng.getrandbits(32),rng.getrandbits(32))]
            records.append({'case':case,'summary':report['summary'],'samples':samples})
        # Two separate conditionals correlate, but the compositional abstraction
        # deliberately treats them as independent and overestimates the total.
        tree=probe.module('swap');f=tree[-2];cond=['i32.and',['local.get','0'],['i32.const','1']]
        f[-2:-1]=[['if',cond,['then',*probe.blocks([9])],['else',*probe.blocks([1])]],
                  ['call','0',['i32.const','100']],
                  ['if',cond,['then',*probe.blocks([1])],['else',*probe.blocks([9])]]]
        folder=out/'correlated';folder.mkdir();wp=folder/'original.wat';src=folder/'original.wasm'
        wp.write_text(t.w.emit(tree),encoding='utf8');t.w.tool('wat2wasm',[wp,'-o',src])
        rr=t.transform(src,folder/'frontier.wasm','frontier')
        vals=[probe.oracle(tree,[secret,42]) for secret in range(4)]
        corr={'summary':rr['summary'],'concreteMax':max(x['prefix'][-1] for x in vals),'oracle':vals}
        manifest={'seed':2026102407,'records':records,'correlated':corr}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
        r=subprocess.run(['node',str(HERE/'audit.cjs'),str(out)],capture_output=True,text=True,timeout=60)
        (out/'run.json').write_text(json.dumps({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode: raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
