import argparse,json,random,statistics,subprocess
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
def instrument(src,dst):
    m=p.q.read(src);m.append(['func',['export','"bench"'],['param','i32','i64'],['result','i64'],['block',['loop',['br_if','1',['i32.eqz',p.g(0)]],['local.set','1',['call','0',['i64.xor',p.g(1),p.c(0x9e3779b97f4a7c15,'i64')]]],['local.set','0',['i32.sub',p.g(0),p.c(1)]],['br','0']]],p.g(1)]);p.q.compile(p.w.emit(m),dst)
def main(data,out,reuse_runtime=None):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);m=json.loads((data/'manifest.json').read_text());rs=[r for r in m['rows'] if r['opt']];jobs=[(r,i) for r in rs for i in range(3)]
    reuse=None
    if reuse_runtime:
        old=Path(reuse_runtime);protocol=json.loads((old/'protocol.json').read_text());assert protocol['bench_sha256']==p.q.digest(HERE/'bench.cjs')
        for r in rs:
            instrument(data/r['file'],out/r['file']);assert p.q.digest(out/r['file'])==p.q.digest(old/r['file'])
        runtime=json.loads((old/'runtime.json').read_text());reuse=dict(source=str(old),runtime_sha256=p.q.digest(old/'runtime.json'),instrumented_byte_matches=len(rs));p.q.save(out/'runtime.json',runtime)
    else:
        for r in rs:instrument(data/r['file'],out/r['file'])
        random.Random(191019).shuffle(jobs);runtime=[]
        for k,(r,rep) in enumerate(jobs):
            a=json.loads(subprocess.check_output(['node',str(HERE/'bench.cjs'),str(out/r['file'])],text=True,timeout=60));runtime.append(dict(a,id=r['id'],n=r['n'],family=r['family'],mode=r['mode'],replicate=rep,bytes=r['bytes']));p.q.save(out/'runtime.json',runtime)
            if k%15==14:print('runtime',k+1,'/',len(jobs),flush=True)
    summary=[]
    for r in rs:
        vals=[x for x in runtime if x['id']==r['id']];meds=[statistics.median(x['ns']) for x in vals];summary.append(dict(id=r['id'],n=r['n'],family=r['family'],mode=r['mode'],ns=statistics.median(meds),process_medians_ns=meds,bytes=r['bytes'],rss_kib=statistics.median(x['peak_rss_kib'] for x in vals)))
    p.q.save(out/'summary.json',summary);analysis=[]
    for r in m['rows']:
        if not r['recovered']:continue
        runs=[]
        for _ in range(5):
            a=p.recover(data/r['file']);code=a.pop('code');assert code==(data/r['recovered']).with_suffix('.wat').read_text();runs.append(a)
        analysis.append(dict(id=r['id'],n=r['n'],family=r['family'],mode=r['mode'],opt=r['opt'],runs=runs));p.q.save(out/'analysis.json',analysis)
    p.q.save(out/'protocol.json',dict(fresh_processes=len(runtime),new_runtime_processes=0 if reuse else len(runtime),runtime_reuse=reuse,analysis_runs=len(analysis)*5,diagnostics=False,benchmark='Wasm internal loop calls run; no post-wrapper O3',order_seed=191019,prototype_sha256=p.q.digest(HERE/'prototype.py'),bench_sha256=p.q.digest(HERE/'bench.cjs')));print('done',len(runtime),len(analysis)*5)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');a.add_argument('--reuse-runtime');v=a.parse_args();main(v.data,v.output,v.reuse_runtime)
