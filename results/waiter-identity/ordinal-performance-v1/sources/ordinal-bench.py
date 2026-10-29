import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess

HERE=Path(__file__).resolve().parent


def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('ordinal-bench.py','ordinal-bench.cjs','ordinal-plan.md','partition.cjs','partition-ordinal.cjs','partition-barrier.cjs'):shutil.copy2(HERE/name,out/'sources'/name)
    modes=('batch','single-deadline','ordinal','registry');tasks=[(m,i) for m in modes for i in range(5)];random.Random(2026102419).shuffle(tasks);raw=[]
    try:
        for mode,i in tasks:
            cmd=['node',str(HERE/'ordinal-bench.cjs'),mode];p=subprocess.run(cmd,capture_output=True,text=True,timeout=60);raw.append({'mode':mode,'replicate':i,'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(out/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf8')
            if p.returncode:raise RuntimeError(p.stderr)
        data=[json.loads(r['stdout']) for r in raw];rows=[]
        for first in data[0]['rows']:
            row={k:first[k] for k in ('n','k','shape')}
            for mode in modes:
                group=[next(r for r in p['rows'] if r['n']==first['n'] and r['shape']==first['shape']) for p in data if p['mode']==mode];samples=[r['median'] for r in group];q=statistics.quantiles(samples,n=4,method='inclusive');row[mode]={'medianMs':statistics.median(samples),'q1':q[0],'q3':q[2],'processMedians':samples,'registrations':group[0]['registrations'],'notifications':group[0]['notifications']}
            rows.append(row)
        (out/'results.json').write_text(json.dumps({'seed':2026102419,'processes':len(raw),'rows':rows,'limitation':'One JS engine. Fresh private memories, quiescent. Single-deadline controls timer allocation; registry is prepopulated and uses Map. Not comparable as repeated samples of the earlier 3-warmup benchmark.'},indent=2),encoding='utf8');print(json.dumps({'processes':len(raw),'rows':len(rows)}))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);main(p.parse_args().output.resolve())
