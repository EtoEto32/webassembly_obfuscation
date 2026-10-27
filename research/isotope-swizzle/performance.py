import argparse,json,random,statistics,subprocess
from pathlib import Path
import prototype as q
HERE=Path(__file__).resolve().parent
def main(data,out):
    data=Path(data);out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=json.loads((data/'manifest.json').read_text());jobs=[]
    for row in rows:
        for key in (['file','recovered'] if row['mode']=='table' else ['file']):
            for i in range(3):jobs.append((row,key,i))
    random.Random(191026).shuffle(jobs);native=[]
    for row,key,i in jobs:
        v=json.loads(subprocess.check_output(['node',str(HERE/'bench.cjs'),str(data/row[key])],text=True,timeout=30));v.update(file=row[key],replicate=i);native.append(v)
    q.save(out/'native.json',native);analysis=[]
    for row in rows:
        runs=[q.lower(data/row['file']) for _ in range(7)];analysis.append(dict(file=row['file'],runs=runs))
    q.save(out/'analysis.json',analysis);summary=[]
    for row in rows:
        for key in (['file','recovered'] if row['mode']=='table' else ['file']):
            runs=[v for v in native if v['file']==row[key]];a=next(v['runs'] for v in analysis if v['file']==row['file'])
            meds=[statistics.median(v['ns']) for v in runs]
            summary.append(dict(file=row[key],kernel=row['kernel'],mode=row['mode'] if key=='file' else 'recovered',seed=row['seed'],opt=row['opt'],bytes=(data/row[key]).stat().st_size,ns=statistics.median(meds),process_medians_ns=meds,peak_rss_kib=statistics.median(v['peak_rss_kib'] for v in runs),compile_ms=statistics.median(v['compile_ms'] for v in runs),instantiate_ms=statistics.median(v['instantiate_ms'] for v in runs),read_ms=statistics.median(v['read_ms'] for v in a) if key=='file' else None,normalize_rewrite_ms=statistics.median(v['normalize_rewrite_ms'] for v in a) if key=='file' else None))
    q.save(out/'summary.json',summary);print(json.dumps(dict(fresh_processes=len(native),analysis_runs=len(rows)*7)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('data');p.add_argument('output');v=p.parse_args();main(v.data,v.output)
