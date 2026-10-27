"""Isolated two-engine comparison of original and retained lifetime states."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main(source,out):
    source=source.resolve();out.mkdir(parents=True,exist_ok=False);logs=[];rows=[];failures=[]
    for name,value in json.loads((source/'sha256.json').read_text()).items():assert digest(source/name)==value
    preflight=subprocess.run([sys.executable,str(HERE/'post-start-live-preflight.py')],capture_output=True,text=True,encoding='utf8',timeout=30)
    (out/'preflight.json').write_text(json.dumps({'code':preflight.returncode,'stdout':preflight.stdout,'stderr':preflight.stderr},indent=2));assert preflight.returncode==0,preflight.stderr
    assert json.loads(preflight.stdout.splitlines()[0])['enoughForSequentialOneGiB'],'not enough free physical memory'
    for engine in ('Node','Wasmtime'):
        for variant in ('original','retained'):
            target=out/(engine.lower()+'-'+variant+'.json')
            cmd=['node',str(HERE/'post-start-live.mjs'),str(source),variant,str(target)] if engine=='Node' else [sys.executable,str(HERE/'post-start-live-worker.py'),str(source),variant,str(target)]
            try:
                run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=180);logs.append({'engine':engine,'variant':variant,'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
                if run.returncode:failures.append({'engine':engine,'variant':variant,'status':'worker-error'})
                else:rows.append(json.loads(target.read_text()));print(run.stdout,flush=True)
            except subprocess.TimeoutExpired:failures.append({'engine':engine,'variant':variant,'status':'timeout'})
    static=subprocess.run([str(ROOT/'.tools/state-witness-census-graph-target/release/wasm-lifetime-census.exe'),str(source/'retained.wasm')],capture_output=True,text=True,encoding='utf8',timeout=60)
    assert static.returncode==0,static.stderr;scan=json.loads(static.stdout);assert scan['status']=='complete' and scan['postInstantiation']['allLifetimeDifferencesIrrelevant']
    (out/'retained-scan.json').write_text(static.stdout)
    if len(rows)==4:
        for key in ('memoryBytes','memoryBefore','memoryAfter','tableSizes','pureConstantExports','originalApiCalls','probeCalls','importCalls'):
            assert all(r[key]==rows[0][key] for r in rows),key
    result={'rows':[{k:v for k,v in row.items() if k!='outcomes'} for row in rows],'failures':failures,'logs':logs,'source':str(source),'sourceManifestSha256':digest(source/'manifest.json'),
        'scope':'Controlled drop omission in real ffmpeg binary; no video workload, real restorer, concurrent worker, or original exported API execution when no pure constant exports were found.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('post-start-live.py','post-start-live.mjs','post-start-live-worker.py','post-start-live-preflight.py','post-start-live-bindings.py','post-start-live-plan.md'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:digest(p) for p in out.iterdir()},indent=2));print(json.dumps({'completed':len(rows),'failures':failures}))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
