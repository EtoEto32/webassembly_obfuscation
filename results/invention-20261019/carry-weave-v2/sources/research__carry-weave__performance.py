import argparse,json,random,statistics,subprocess
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
def main(data,out):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);rows=json.loads((data/'manifest.json').read_text());jobs=[(r,i) for r in rows if r['opt']=='O3' for i in range(3)];random.Random(191019).shuffle(jobs);native=[]
    for r,i in jobs:
        a=json.loads(subprocess.check_output(['node',str(HERE/'bench.cjs'),str(data/r['file'])],text=True,timeout=60));native.append(dict(a,file=r['file'],n=r['n'],kind=r['kind'],mode=r['mode'],replicate=i))
    p.save(out/'native.json',native);summary=[]
    for r in rows:
        if r['opt']!='O3':continue
        runs=[x for x in native if x['file']==r['file']];meds=[statistics.median(x['ns']) for x in runs]
        summary.append(dict(file=r['file'],n=r['n'],kind=r['kind'],mode=r['mode'],ns=statistics.median(meds),process_medians_ns=meds,bytes=r['bytes'],rss_kib=statistics.median(x['peak_rss_kib'] for x in runs)))
    p.save(out/'summary.json',summary);analysis=[]
    for r in rows:
        runs=[p.recover(data/r['file']) for _ in range(5)];assert all(x['terms']==r['attack']['terms'] for x in runs)
        analysis.append(dict(file=r['file'],n=r['n'],kind=r['kind'],mode=r['mode'],opt=r['opt'],runs=[{k:v for k,v in x.items() if k!='terms'} for x in runs]))
    p.save(out/'analysis.json',analysis);p.save(out/'protocol.json',dict(fresh_processes=len(native),analysis_runs=len(rows)*5,bench_sha256=p.digest(HERE/'bench.cjs'),extractor_sha256=p.digest(HERE/'prototype.py')));print(json.dumps(dict(fresh_processes=len(native),analysis_runs=len(rows)*5)))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
