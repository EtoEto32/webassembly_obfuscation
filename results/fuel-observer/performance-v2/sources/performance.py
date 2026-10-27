import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import transform as t

HERE=Path(__file__).resolve().parent


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('performance.py','performance.cjs','guard.cjs','transform.py'):shutil.copy2(HERE/name,out/'sources'/name)
    staging=out/'inputs';staging.mkdir();shutil.copy2(source/'manifest.json',staging/'manifest.json')
    for rec in json.loads((source/'manifest.json').read_text())['records']:
        dest=staging/rec['kind'];dest.mkdir()
        for name in ('target-O3.wasm','target.json','original.wasm'):shutil.copy2(source/rec['kind']/name,dest/name)
        t.w.tool('wasm-opt',[dest/'original.wasm','-O3','-o',dest/'original-O3.wasm'])
    modes=['original','whole-host','whole','depth','observer'];tasks=[(m,i) for m in modes for i in range(5)];rng=random.Random(2026102413);rng.shuffle(tasks);raw=[]
    try:
        for mode,i in tasks:
            cmd=['node',str(HERE/'performance.cjs'),str(staging),mode,str(i)];p=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            row={'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr};raw.append(row);(out/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf8')
            if p.returncode:raise RuntimeError(p.stderr)
            print(mode,i,flush=True)
        parsed=[json.loads(x['stdout']) for x in raw];summary=[]
        for kind in [x['kind'] for x in parsed[0]['rows']]:
            row={'kind':kind}
            for mode in modes:
                xs=[next(v for v in p['rows'] if v['kind']==kind)['median'] for p in parsed if p['mode']==mode];q=statistics.quantiles(xs,n=4,method='inclusive');row[mode]={'median':statistics.median(xs),'q1':q[0],'q3':q[2],'processMedians':xs}
            summary.append(row)
        (out/'results.json').write_text(json.dumps({'seed':2026102413,'processes':len(raw),'rows':summary,'limitation':'All modes use O3. No physical CPU fuel protection. Whole-host reserves once before calling the original binary; it has no intermediate progress. Per-process memory metrics aggregate seven fixtures.'},indent=2),encoding='utf8')
        (out/'input-sha256.json').write_text(json.dumps({str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file() and p.suffix in ('.json','.wasm')},indent=2),encoding='utf8')
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();main(a.source.resolve(),a.output.resolve())
