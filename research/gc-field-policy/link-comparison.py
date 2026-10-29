import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import sys
from workload import ROOT,HERE,CHECK,command,expected,w


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);commands=[]
    lib=source/'accessor-lib.wasm';consumer=source/'accessor-client.wasm';policy=source/'accessor-policy.json'
    c=command([CHECK,lib,policy,consumer]);commands.append(c);assert c['code']==0,c
    assert next(r['accepted'] for r in json.loads(c['stdout'])['results'] if r['mode']=='closure')
    config=w.Config();config.wasm_gc=True;config.wasm_function_references=True;engine=w.Engine(config)
    assert all(i.module=='lib' and i.name in ['refresh','x','y'] for i in w.Module.from_file(engine,consumer).imports)
    merged=out/'accessor-merged.wasm';optimized=out/'accessor-merged-o3.wasm';bin=ROOT/'.tools/binaryen-version_133/bin'
    features=['--mvp-features','--enable-reference-types','--enable-gc']
    c=command([bin/'wasm-merge.exe',lib,'lib',consumer,'client',*features,'-o',merged]);commands.append(c);(out/'commands.json').write_text(json.dumps(commands,indent=2));assert c['code']==0,c
    c=command([bin/'wasm-opt.exe',merged,*features,'-O3','-o',optimized]);commands.append(c);(out/'commands.json').write_text(json.dumps(commands,indent=2));assert c['code']==0,c
    jobs=[(f,engine,p,repeat) for f in (merged,optimized) for engine in ('Node','Wasmtime') for p in (1,8) for repeat in range(3)]
    random.Random(261027).shuffle(jobs);rows=[]
    for file,engine,passes,repeat in jobs:
        args=['node',HERE/'link-bench.mjs'] if engine=='Node' else [sys.executable,HERE/'link-bench.py']
        c=command(args+[file,passes]);commands.append(c);(out/'commands.json').write_text(json.dumps(commands,indent=2));assert c['code']==0,c
        r=json.loads(c['stdout']);assert r['checks']==expected(65536,passes) and r['privateAfter']==77123,r
        rows.append(dict(file=file.name,passes=passes,repeat=repeat,**r))
    summary=[]
    for f in (merged,optimized):
        for engine in ('Node','Wasmtime'):
            for passes in (1,8):
                rs=[r for r in rows if (r['file'],r['engine'],r['passes'])==(f.name,engine,passes)]
                ms=[statistics.median(r['samples']) for r in rs]
                summary.append(dict(file=f.name,engine=engine,passes=passes,medianMs=statistics.median(ms),processMedians=ms,bytes=f.stat().st_size))
    (out/'measurements.json').write_text(json.dumps(rows,indent=2));(out/'commands.json').write_text(json.dumps(commands,indent=2))
    (out/'summary.json').write_text(json.dumps(dict(processes=len(jobs),n=65536,stride=1,warmups=12,samples=11,rows=summary),indent=2))
    sources=out/'sources';sources.mkdir()
    for f in (HERE/'link-plan.md',HERE/'link-comparison.py',HERE/'link-bench.mjs',HERE/'link-bench.py',HERE/'workload.py',lib,consumer,policy):shutil.copyfile(f,sources/f.name)
    (out/'hashes.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.source,a.out)
