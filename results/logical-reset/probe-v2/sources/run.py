import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import prototype as p
from fixtures import fixtures

HERE=Path(__file__).resolve().parent

def observe(src,dst):
    m=p.read(src)
    m.extend([['export','"__test_mem"',['memory','0']],['export','"__test_table"',['table','0']]])
    p.compile_wat(p.w.emit(m),dst)

def main(out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('prototype.py','fixtures.py','run.py','run.cjs','plan.md'):
        shutil.copy2(HERE/name,out/'sources'/name)
    shutil.copy2(p.ROOT/'research/connectivity-elimination/prototype.py',out/'sources/wat-common.py')
    manifest={'directory':str(out.resolve()),'rows':[],'optimizerFailures':[]};start=time.perf_counter()
    try:
        for f in fixtures():
            name=f['name'];source=out/(name+'-source.wasm');p.compile_wat(f['wat'],source)
            for mode in ('source','full','plain','no-bounds','no-drop'):
                target=source if mode=='source' else out/(name+'-'+mode+'.wasm')
                meta={'mode':mode} if mode=='source' else p.transform(source,target,mode)
                optimized=target.with_name(target.stem+'-O3.wasm')
                pipelines=[('raw',target)]
                try:
                    p.tool('wasm-opt',[target,'-O3','--enable-bulk-memory','--enable-reference-types','-o',optimized])
                    pipelines.append(('O3',optimized))
                except RuntimeError as error:
                    manifest['optimizerFailures'].append({'fixture':name,'mode':mode,'error':str(error)})
                for pipeline,path in pipelines:
                    obs=path.with_name(path.stem+'-observed.wasm');observe(path,obs)
                    manifest['rows'].append({'fixture':name,'mode':mode,'pipeline':pipeline,'file':path.name,'observed':obs.name,
                                             'bytes':path.stat().st_size,'transform':meta})
        manifest['generationSeconds']=time.perf_counter()-start
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        q=subprocess.run(['node',str(HERE/'run.cjs'),str(out/'manifest.json')],capture_output=True,text=True,encoding='utf-8',timeout=120)
        (out/'node.stdout.log').write_text(q.stdout,encoding='utf-8');(out/'node.stderr.log').write_text(q.stderr,encoding='utf-8')
        if q.returncode:raise RuntimeError(q.stderr or q.stdout)
        result=json.loads(q.stdout);(out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    except Exception as e:
        (out/'error.json').write_text(json.dumps({'type':type(e).__name__,'error':str(e)},indent=2),encoding='utf-8');raise
    finally:
        hashes={str(x.relative_to(out)).replace('\\','/'):hashlib.sha256(x.read_bytes()).hexdigest() for x in out.rglob('*') if x.is_file()}
        (out/'sha256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args();main(a.out)
