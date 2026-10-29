import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import time
import probe as p
import transform as t

HERE=Path(__file__).resolve().parent


def tree(count,reveals,rng):
    base=p.fixture('no-event');f=next(x for x in base[1:] if x[0]=='func');body=[]
    for i in range(count):
        a,b=p.work(rng.randrange(1,4)),p.work(rng.randrange(1,4))
        if i in reveals:a+=[p.mark(100+i,1)];b+=[p.mark(100+i,0)]
        body.append(p.branch(1<<(i%8),a,b))
    f[:]=['func',['param','i32','i32'],['result','i32'],['local','i32'],['local.set','2',['local.get','1']],*body,['local.get','2']]
    return base


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('merge-audit.py','merge-audit.cjs','guard.cjs','probe.py','transform.py'):shutil.copy2(HERE/name,out/'sources'/name)
    rng=random.Random(2026102414);rows=[]
    try:
        settings=[(i%5+5,sorted(rng.sample(range(i%5+5),i%3))) for i in range(24)]+[(n,rs) for n in (16,24,32) for rs in ([],[0,7])]
        for k,(count,reveals) in enumerate(settings):
            folder=out/str(k);folder.mkdir();m=tree(count,reveals,rng);src=folder/'original.wasm';(folder/'original.wat').write_text(t.w.emit(m),encoding='utf8');t.w.tool('wat2wasm',[folder/'original.wat','-o',src])
            begin=time.perf_counter();a=t.transform(src,folder/'merged.wasm',True);mergedSeconds=time.perf_counter()-begin
            if count<=12:
                begin=time.perf_counter();b=t.transform(src,folder/'enumerated.wasm',False);enumeratedSeconds=time.perf_counter()-begin
                for key in ('nodes','whole','depthBounds','terminalBounds','pathCount'):assert a[key]==b[key],(k,key)
                assert (folder/'merged.wasm').read_bytes()==(folder/'enumerated.wasm').read_bytes();status='equal'
            else:
                begin=time.perf_counter()
                try:t.analyze(src,False)
                except ValueError as e:
                    if str(e)!='path/event budget exceeded':raise
                    status='enumeration-budget-rejection'
                else:raise AssertionError('expected enumeration budget rejection')
                enumeratedSeconds=time.perf_counter()-begin
            oracle=[{'secret':s,'x':rng.getrandbits(32)} for s in [0,1,2,3,127,128,255,0xffffffff]+[rng.getrandbits(32) for _ in range(56)]]
            for case in oracle:case.update(p.interpret(m,case['secret'],case['x']))
            (folder/'oracle.json').write_text(json.dumps(oracle,indent=2),encoding='utf8')
            rows.append({'id':k,'branches':count,'reveals':reveals,'representedPaths':a['pathCount'],'rows':a['rowCount'],'nodes':len(a['nodes']),'status':status,'mergedSeconds':mergedSeconds,'enumeratedSeconds':enumeratedSeconds,'bytes':a['targetBytes'],'sidecarBytes':(folder/'merged.json').stat().st_size})
        (out/'manifest.json').write_text(json.dumps({'seed':2026102414,'rows':rows},indent=2),encoding='utf8')
        cmd=['node',str(HERE/'merge-audit.cjs'),str(out)];r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (out/'run.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        print(r.stdout)
    finally:
        (out/'sha256.json').write_text(json.dumps({str(x.relative_to(out)):hashlib.sha256(x.read_bytes()).hexdigest() for x in out.rglob('*') if x.is_file() and x.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
