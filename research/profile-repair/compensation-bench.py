import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess

HERE=Path(__file__).resolve().parent

def stats(values):
    q=statistics.quantiles(values,n=4,method='inclusive')
    return {'median':statistics.median(values),'q1':q[0],'q3':q[2],'processMedians':values}

def main(source,out):
    out.mkdir(parents=True,exist_ok=False)
    for name in ('compensation-bench.py','compensation-bench.cjs','compensation-plan.md'):shutil.copy2(HERE/name,out/name)
    raw=[]
    try:
        for replicate in range(5):
            cmd=['node','--no-liftoff',str(HERE/'compensation-bench.cjs'),str(source/'results.json'),str(replicate)]
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
            raw.append({'command':cmd,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr});(out/'raw.json').write_text(json.dumps(raw,indent=2),encoding='utf8')
            if run.returncode:raise RuntimeError(run.stderr)
        data=[json.loads(r['stdout']) for r in raw];rows=[]
        for item in sorted(data[0]['rows'],key=lambda r:(r['n'],r['name'])):
            name,n=item['name'],item['n'];values=[next(r['medianNsPerByte'] for r in d['rows'] if r['name']==name and r['n']==n) for d in data]
            baseline='strict-0' if name.endswith('-0') else 'strict-native'
            denominators=[next(r['medianNsPerByte'] for r in d['rows'] if r['name']==baseline and r['n']==n) for d in data]
            rows.append({'name':name,'n':n,'nsPerByte':stats(values),'pairedToStrict':stats([a/b for a,b in zip(values,denominators)])})
        init={name:stats([d['init'][name]['medianNs'] for d in data]) for name in data[0]['init']}
        report={'processes':5,'rounds':15,'warmupRounds':2,'bytesPerSample':1048576,'rows':rows,'initNs':init,'sourceManifestSHA256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
           'note':'Optimized actual Wasm; paired shuffled order, same-binary adaptiveCopy calibration. Small batches include JS call overhead; init reported separately. Explicit R0 lowering is not a second hardware architecture. No physical constant-time conclusion.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'processes':5,'rows':len(rows),'largeBatch':[r for r in rows if r['n']==65536]}))
    finally:(out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
