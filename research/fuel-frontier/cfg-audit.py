"""Validate label-depth and early-return handling using independent execution."""
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
    for n in ('cfg-audit.py','cfg-audit.cjs','acyclic.py','transform.py','probe.py','release-plan.md'):
        shutil.copy2(HERE/n,out/'sources'/n)
    rng=random.Random(2026102408);records=[]
    cond=['i32.and',['local.get','0'],['i32.const','1']]
    mark=['call','0',['i32.const','100'],['i32.shr_u',['local.get','2'],['i32.const','28']]]
    try:
        for case in range(32):
            a,b=rng.randrange(1,8),rng.randrange(1,8);kind=case%4
            sa=probe.blocks([a]);sb=probe.blocks([b]);ret=['return',['local.get','2']]
            if kind==0:
                middle=[['block',['if',cond,['then',*sa,mark,['br','1']]],*sb,mark]]
            elif kind==1:
                middle=[['block',*sa,['br_if','0',cond],*sb],mark]
            elif kind==2:
                middle=[['if',cond,['then',*sa,mark,ret],['else',*sb,mark,ret]]]
            else:
                middle=[['block',['block',['if',cond,['then',*sa,mark,['br','2']]],*sb,mark,['br','1']],['call','0',['i32.const','999'],['i32.const','0']]]]
            tree=['module',['type',['func',['param','i32','i32']]],['import','"env"','"mark"',['func',['type','0']]],
                  ['func',['param','i32','i32'],['result','i32'],['local','i32'],['local.set','2',['local.get','1']],*middle,ret],['export','"run"',['func','1']]]
            folder=out/str(case);folder.mkdir();wp=folder/'original.wat';src=folder/'original.wasm';wp.write_text(t.w.emit(tree),encoding='utf8');t.w.tool('wat2wasm',[wp,'-o',src])
            modes={mode:t.transform(src,folder/(mode+'.wasm'),mode,True,True) for mode in t.MODES}
            for mode in ('frontier','late'):
                t.w.tool('wasm-opt',[folder/(mode+'.wasm'),'-O3','-o',folder/(mode+'-O3.wasm')]);t.w.tool('wasm-validate',[folder/(mode+'-O3.wasm')])
            samples=[{'args':[secret,payload],'expected':probe.oracle(tree,[secret,payload])} for secret in range(4) for payload in (0,1,0x80000000,0xffffffff,rng.getrandbits(32))]
            records.append({'case':case,'kind':kind,'summary':modes['frontier']['summary'],'samples':samples})
        (out/'manifest.json').write_text(json.dumps({'seed':2026102408,'records':records},indent=2),encoding='utf8')
        r=subprocess.run(['node',str(HERE/'cfg-audit.cjs'),str(out)],capture_output=True,text=True,timeout=60)
        (out/'run.json').write_text(json.dumps({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
