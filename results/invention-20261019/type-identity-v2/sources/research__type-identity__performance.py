import argparse,json,random,statistics,subprocess
from pathlib import Path
import prototype as q
HERE=Path(__file__).resolve().parent
def main(main,out):
    main=Path(main);out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=json.loads((main/'manifest.json').read_text());work=[(r,k) for r in rows for k in range(3)];random.Random(1910).shuffle(work);data=[]
    for row,k in work:
        run=json.loads(subprocess.check_output(['node',str(HERE/'bench.cjs'),str(main/row['file'])],text=True,timeout=30));run.update(file=row['file'],replicate=k);data.append(run)
    q.save(out/'native.json',data);analysis=[]
    for row in rows:
        rs=[q.lower(main/row['file'],None) for _ in range(7)]
        analysis.append(dict(file=row['file'],read_ms=[x['read_canonicalize_ms'] for x in rs],lower_ms=[x['lower_ms'] for x in rs]))
    q.save(out/'analysis.json',analysis);summary=[]
    for row in rows:
        runs=[x for x in data if x['file']==row['file']];a=next(x for x in analysis if x['file']==row['file']);meds=[statistics.median(x['ns']) for x in runs]
        summary.append(dict(file=row['file'],kernel=row['kernel'],mode=row['mode'],groups=row['groups'],siblings=row['siblings'],opt=row['opt'],ns=statistics.median(meds),process_medians_ns=meds,compile_ms=statistics.median(x['compile_ms'] for x in runs),instantiate_ms=statistics.median(x['instantiate_ms'] for x in runs),peak_rss_kib=statistics.median(x['peak_rss_kib'] for x in runs),bytes=row['bytes'],read_ms=statistics.median(a['read_ms']),lower_ms=statistics.median(a['lower_ms'])))
    q.save(out/'summary.json',summary);print(json.dumps(dict(fresh_processes=len(data),analysis_runs=len(rows)*7)))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('main');a.add_argument('output');v=a.parse_args();main(v.main,v.output)
