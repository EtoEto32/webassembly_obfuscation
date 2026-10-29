import argparse,json,random,statistics,subprocess,time
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
def main(data,out,analysis_from=None):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);m=json.loads((data/'manifest.json').read_text());rs=[r for r in m['rows'] if r['opt']];sources={r['source']:r for r in rs};jobs=[(r,'component',i) for r in rs for i in range(3)]+[(r,'core',i) for r in sources.values() for i in range(3)];random.Random(191019).shuffle(jobs);rows=[]
    for ix,(r,kind,i) in enumerate(jobs):
        file=data/(r['source'] if kind=='core' else r['js']);run=json.loads(subprocess.check_output(['node','--expose-gc',str(HERE/'bench.cjs'),kind,str(file)],text=True,timeout=60))
        rows.append(dict(run,id=r['id'] if kind=='component' else r['source'],n=r['n'],family=r['family'],mode=r['mode'] if kind=='component' else 'core',replicate=i));p.q.save(out/'runtime.json',rows)
        if ix%15==14:print('runtime',ix+1,'/',len(jobs),flush=True)
    analysis=[]
    if analysis_from:
        old=Path(analysis_from);oldprotocol=json.loads((old/'protocol.json').read_text())
        assert oldprotocol['extractor_sha256']==p.q.digest(HERE/'prototype.py')
        analysis=json.loads((old/'analysis.json').read_text())
        assert {r['id'] for r in analysis}=={r['id'] for r in m['rows']}
        assert all(p.q.digest(data/r['component'])==r['sha256'] for r in m['rows'])
        p.q.save(out/'analysis.json',analysis)
    for r in ([] if analysis_from else m['rows']):
        reads=[];a=[];ref=None
        for rep in range(5):
            start=time.perf_counter();tree,mods=p.read_component(data/r['component']);reads.append((time.perf_counter()-start)*1000)
            start=time.perf_counter();ev=p.Evaluator(tree,mods);expr,stats=ev.recover();code=p.w.emit(p.mod(expr));a.append((time.perf_counter()-start)*1000)
            if ref is None:ref=code
            assert ref==code
        analysis.append(dict(id=r['id'],n=r['n'],family=r['family'],mode=r['mode'],opt=r['opt'],read_ms=reads,recovery_ms=a,stats=stats));p.q.save(out/'analysis.json',analysis)
    summary=[]
    for rid in sorted(set(r['id'] for r in rows)):
        rs=[r for r in rows if r['id']==rid];r=rs[0];meds=[statistics.median(x['ns']) for x in rs]
        summary.append(dict(id=rid,n=r['n'],family=r['family'],mode=r['mode'],ns=statistics.median(meds),process_medians_ns=meds,peak_rss_kib=statistics.median(x['peak_rss_kib'] for x in rs),heap_used_bytes=statistics.median(x['after']['heapUsed'] for x in rs),array_buffers_bytes=statistics.median(x['after']['arrayBuffers'] for x in rs)))
    p.q.save(out/'summary.json',summary);p.q.save(out/'protocol.json',dict(fresh_processes=len(rows),analysis_runs=len(analysis)*5,analysis_reused_from=str(analysis_from) if analysis_from else None,bench_sha256=p.q.digest(HERE/'bench.cjs'),extractor_sha256=p.q.digest(HERE/'prototype.py'),reader='Jco print + WABT wasm2wat/validate per embedded module',analysis='symbolic core/canonical evaluation plus WAT serialization',runtime_order_seed=191019));print('done',len(rows),len(analysis)*5)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');a.add_argument('--analysis-from');v=a.parse_args();main(v.data,v.output,v.analysis_from)
