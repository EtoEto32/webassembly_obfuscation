import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import sys
from experiment import ROOT,HERE,WAT,VALIDATE,REWRITE,run

def source(shape):
    funcs=[]
    for i in range(8):
        funcs.append(f'(func $s{i} (type $f) local.get 0 i32.const {1664525+2*i} i32.mul i32.const {1013904223+i} i32.add i32.const {i+1} i32.rotl)')
    calls=[]
    for i in range(8):
        if shape=='indirect' or shape=='mixed' and i>=4:
            calls.append(f'local.get 2 local.get 3 i32.const {i} i32.add i32.const 7 i32.and call_indirect (type $f) local.set 2')
        else: calls.append(f'local.get 2 call $s{i} local.set 2')
    table='' if shape=='direct-private' else '(table 8 funcref) (elem (i32.const 0) func '+ ' '.join(f'$s{i}' for i in range(8))+')'
    return f'''(module (type $f (func (param i32) (result i32))) {' '.join(funcs)} {table}
      (func (export "run") (param i32 i32) (result i32) (local i32 i32)
        local.get 1 local.set 2
        block $done loop $again
          local.get 3 local.get 0 i32.ge_u br_if $done
          {' '.join(calls)}
          local.get 3 i32.const 1 i32.add local.set 3 br $again
        end end local.get 2))'''

def main(out):
    out.mkdir(parents=True,exist_ok=False);cases=[];commands=[]
    for shape in ('direct-private','direct-address','indirect','mixed'):
        wat=out/(shape+'.wat');wat.write_text(source(shape));binary=out/(shape+'.wasm')
        c=run([WAT,wat,'-o',binary]);commands.append(c);assert c['code']==0,c
        for mode in ('original','entry','address','refs'):
            target=binary;transform=None
            if mode!='original':
                target=out/(shape+'-'+mode+'.wasm')
                c=run([REWRITE,mode,binary,target]);commands.append(c);assert c['code']==0,c
                transform=json.loads(c['stdout'])
            c=run([VALIDATE,target]);commands.append(c);assert c['code']==0,c
            cases.append(dict(shape=shape,mode=mode,path=str(target.resolve()),bytes=target.stat().st_size,transform=transform))
    jobs=[(case,engine,repeat) for case in cases for engine in ('Node','Wasmtime') for repeat in range(3)]
    random.Random(251025).shuffle(jobs);measurements=[]
    for case,engine,repeat in jobs:
        args=['node',HERE/'bench.mjs'] if engine=='Node' else [sys.executable,HERE/'bench.py']
        c=run(args+[case['path'],'200000']);commands.append(c);assert c['code']==0,c
        measurements.append(dict(shape=case['shape'],mode=case['mode'],repeat=repeat,**json.loads(c['stdout'])))
        (out/'measurements.json').write_text(json.dumps(measurements,indent=2))
    summary=[]
    for engine in ('Node','Wasmtime'):
        for case in cases:
            rows=[r for r in measurements if r['engine']==engine and r['shape']==case['shape'] and r['mode']==case['mode']]
            target=next(r['checks'] for r in measurements if r['engine']==engine and r['shape']==case['shape'] and r['mode']=='original')
            assert all(r['checks']==target for r in rows)
            times=[statistics.median(r['samples']) for r in rows]
            pooled=[x for r in rows for x in r['samples']]
            quartiles=statistics.quantiles(pooled,n=4,method='inclusive')
            summary.append(dict(engine=engine,shape=case['shape'],mode=case['mode'],medianMs=statistics.median(times),
                processMedians=times,pooledIqrMs=quartiles[2]-quartiles[0],bytes=case['bytes'],
                medianSetupMs=statistics.median(r['setupMs'] for r in rows),peakBytes=max(r['peakBytes'] for r in rows),
                transform=case['transform']))
    for shape in ('direct-private','direct-address','indirect','mixed'):
        checks={tuple(r['checks']) for r in measurements if r['shape']==shape}
        assert len(checks)==1,(shape,checks)
    sources=out/'sources';sources.mkdir()
    for p in (HERE/'performance.py',HERE/'experiment.py',HERE/'bench.py',HERE/'bench.mjs',HERE/'performance-plan.md',HERE/'rewriter/src/main.rs',HERE/'rewriter/Cargo.toml',HERE/'rewriter/Cargo.lock'):
        shutil.copyfile(p,sources/p.name)
    (out/'commands.json').write_text(json.dumps(commands,indent=2))
    (out/'summary.json').write_text(json.dumps(dict(processes=len(jobs),warmups=12,repetitions=11,iterations=200000,seed=251025,rows=summary),indent=2))
    hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
    (out/'hashes.json').write_text(json.dumps(hashes,indent=2))
    for row in summary:print(row['engine'],row['shape'],row['mode'],round(row['medianMs'],3),row['bytes'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
