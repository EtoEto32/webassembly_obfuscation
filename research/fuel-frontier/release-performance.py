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
MODES=('original','dynamic','late','whole','segment','frontier','manual')


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for n in ('release-performance.py','release-performance.cjs','release-performance-plan.md','transform.py','acyclic.py'):
        shutil.copy2(HERE/n,out/'sources'/n)
    staging=out/'inputs';staging.mkdir();shutil.copy2(source/'manifest.json',staging/'manifest.json')
    mf=json.loads((source/'manifest.json').read_text());names=[r['name'] for r in mf['records'] if r['status']=='accepted']
    order=[(mode,i) for mode in MODES for i in range(5)];random.Random(2026102409).shuffle(order)
    raw=[]
    try:
        for name in names:
            for mode in MODES[:-1]:
                src=source/(name+('' if mode=='original' else '-'+mode)+'.wasm');dest=staging/(name+'-'+mode+'.wasm')
                t.w.tool('wasm-opt',[src,'-O3','-o',dest]);t.w.tool('wasm-validate',[dest])
        for mode,rep in order:
            cmd=['node','--expose-gc',str(HERE/'release-performance.cjs'),str(staging),mode]
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
            (out/(mode+'-'+str(rep)+'.log.json')).write_text(json.dumps({'command':cmd,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2),encoding='utf8')
            if run.returncode:raise RuntimeError(run.stderr)
            r=json.loads(run.stdout);r['rep']=rep;raw.append(r);(out/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf8')
        summary=[]
        for name in names:
            values={mode:[r for p in raw if p['mode']==mode for r in p['rows'] if r['name']==name] for mode in MODES}
            assert len({r['checksum'] for rows in values.values() for r in rows})==1
            for mode,rows in values.items():
                ns=[r['medianNs'] for r in rows];q=statistics.quantiles(ns,n=4,method='inclusive')
                summary.append({'name':name,'mode':mode,'medianNs':statistics.median(ns),'q1Ns':q[0],'q3Ns':q[2],'bytes':rows[0]['bytes'],'charges':rows[0]['lastCharges']})
        report={'source':str(source),'seed':2026102409,'order':order,'warmup':2000,'repeats':9,'callsPerRepeat':5000,'summary':summary}
        (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        print(json.dumps(summary))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
