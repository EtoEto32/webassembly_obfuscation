import argparse,json,random,statistics,subprocess
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
def main(data,out):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);rows=json.loads((data/'manifest.json').read_text());jobs=[(r,t,i) for r in rows if r['opt']=='O3' for t in (8,256) for i in range(3)];random.Random(191026).shuffle(jobs);native=[]
    for r,t,i in jobs:
        a=json.loads(subprocess.check_output(['node',str(HERE/'bench.cjs'),str(data/r['file']),str(t)],text=True,timeout=60));native.append(dict(a,file=r['file'],n=r['n'],kind=r['kind'],mode=r['mode'],replicate=i))
    p.save(out/'native.json',native);summaries=[]
    for r in rows:
        if r['opt']!='O3':continue
        for t in (8,256):
            rs=[x for x in native if x['file']==r['file'] and x['rounds']==t];meds=[statistics.median(x['ns']) for x in rs]
            summaries.append(dict(file=r['file'],n=r['n'],kind=r['kind'],mode=r['mode'],rounds=t,ns=statistics.median(meds),process_medians_ns=meds,bytes=r['bytes'],peak_rss_kib=statistics.median(x['peak_rss_kib'] for x in rs),compile_ms=statistics.median(x['compile_ms'] for x in rs),instantiate_ms=statistics.median(x['instantiate_ms'] for x in rs)))
    p.save(out/'summary.json',summaries);analysis=[]
    for r in rows:
        if 'attack' not in r:continue
        rs=[p.extract(data/r['file']) for _ in range(7)];assert all(all(x[k]==r[k] for k in ('n','kind','r','coeff')) for x in rs)
        analysis.append(dict(file=r['file'],n=r['n'],kind=r['kind'],mode=r['mode'],opt=r['opt'],runs=rs))
    p.save(out/'analysis.json',analysis);p.save(out/'protocol.json',dict(fresh_processes=len(native),analysis_runs=sum(len(r['runs']) for r in analysis),bench_sha256=p.digest(HERE/'bench.cjs'),extractor_sha256=p.digest(HERE/'prototype.py')));print(json.dumps(dict(fresh_processes=len(native),analysis_runs=sum(len(r['runs']) for r in analysis))))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
