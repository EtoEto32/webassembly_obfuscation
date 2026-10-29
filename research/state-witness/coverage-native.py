"""Finish the census without disassembly expansion; cross-check completed rows."""
import argparse,collections,concurrent.futures,hashlib,json,shutil,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];EXE=ROOT/'.tools/state-witness-census-target/release/wasm-lifetime-census.exe'
TARGETS=('data.drop','elem.drop','memory.init','table.init')


def inspect(old):
    src=ROOT/old['source'];assert hashlib.sha256(src.read_bytes()).hexdigest()==old['sha256'];start=time.perf_counter()
    try:
        run=subprocess.run([str(EXE),str(src)],capture_output=True,text=True,encoding='utf8',timeout=30)
        result=json.loads(run.stdout) if run.returncode==0 else {'status':'scanner-failure','code':run.returncode,'stderr':run.stderr}
    except subprocess.TimeoutExpired:result={'status':'scanner-timeout'}
    result.update(source=old['source'],sourceURL=old['sourceURL'],corpus=old['corpus'],sha256=old['sha256'],bytes=old['bytes'],previousStatus=old['status'],seconds=time.perf_counter()-start)
    if old['status']=='complete':
        assert result['status']=='complete',result
        assert {n:result['counts'].get(n,0) for n in TARGETS}=={n:old['counts'].get(n,0) for n in TARGETS},old['source']
        result['wabtCountsMatch']=True
    return result


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);old=json.loads((source/'results.json').read_text());rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for row in pool.map(inspect,old['rows']):rows.append(row)
    summary={}
    for corpus in ('nowaset','r3'):
        subset=[r for r in rows if r['corpus']==corpus];complete=[r for r in subset if r['status']=='complete']
        summary[corpus]={'files':len(subset),'statuses':dict(collections.Counter(r['status'] for r in subset)),
            'completeWithPassiveData':sum(any(s['passive'] for s in r['data']) for r in complete),
            'completeWithDrop':sum(any(r['counts'].get(n,0) for n in ('data.drop','elem.drop')) for r in complete),
            'completeWithSharedMemory':sum(any(m['shared'] for m in r['memories']) for r in complete),
            'counts':{n:sum(r['counts'].get(n,0) for r in complete) for n in TARGETS}}
    result={'rows':rows,'summary':summary,'wabtCompletedRowsMatched':sum(r.get('wabtCountsMatch',False) for r in rows),
        'executableSha256':hashlib.sha256(EXE.read_bytes()).hexdigest(),'sourceManifestSha256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
        'scope':'Static scan, native validator accepts all supported features and ignores custom metadata. No reachability or original application execution claim.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    shutil.copy2(__file__,out/'coverage-native.py')
    for name in ('Cargo.toml','Cargo.lock','src/main.rs'):
        dst=out/'census-native'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(HERE/'census-native'/name,dst)
    (out/'sha256.json').write_text(json.dumps({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2));print(json.dumps({'summary':summary,'wabtCompletedRowsMatched':result['wabtCompletedRowsMatched']}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
