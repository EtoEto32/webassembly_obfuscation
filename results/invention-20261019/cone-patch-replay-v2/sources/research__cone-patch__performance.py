import argparse,json,random,statistics,struct,subprocess,time
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
def main(data,out):
    data=Path(data);out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=[r for r in json.loads((data/'manifest.json').read_text()) if r['opt']=='O3'];jobs=[(r,k,i) for r in rows for k in ('bump','coupled','spread') for i in range(3)];random.Random(191026).shuffle(jobs);native=[]
    for r,k,i in jobs:
        v=json.loads(subprocess.check_output(['node',str(HERE/'bench.cjs'),str(data/r['file']),k],text=True,timeout=60));native.append(dict(v,file=r['file'],kernel=k,replicate=i))
    p.save(out/'native.json',native);analysis=[]
    for r in [r for r in json.loads((data/'manifest.json').read_text()) if r['mode']!='plain']:
        # Recover the initial state using only the distributed binary and public layout.
        m=p.read(data/r['file']);state=p.initial(m,r['n']*16*r['records']);runs=[]
        for _ in range(7):
            a=p.extract_config(data/r['file']);t=time.perf_counter();decoded=p.encoded(state,r['n'],a['coeff'],True);a['decode_ms']=(time.perf_counter()-t)*1000;runs.append(a)
        # Ground truth consulted only after recovery, for scoring.
        assert decoded==json.loads((data/r['initial']).read_text())
        analysis.append(dict(file=r['file'],runs=runs,word_count=len(decoded),recovered=True))
    p.save(out/'analysis.json',analysis);summary=[]
    for r in rows:
        for k in ('bump','coupled','spread'):
            runs=[v for v in native if v['file']==r['file'] and v['kernel']==k];med=[statistics.median(v['ns']) for v in runs]
            summary.append(dict(file=r['file'],n=r['n'],depth=r['depth'],mode=r['mode'],kernel=k,bytes=r['bytes'],ns=statistics.median(med),process_medians_ns=med,peak_rss_kib=statistics.median(v['peak_rss_kib'] for v in runs),compile_ms=statistics.median(v['compile_ms'] for v in runs),instantiate_ms=statistics.median(v['instantiate_ms'] for v in runs)))
    p.save(out/'summary.json',summary);print(json.dumps(dict(fresh_processes=len(native),analysis_runs=len(analysis)*7)))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
