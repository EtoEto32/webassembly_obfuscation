import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DEPS=ROOT/'.tools/import-alias-quotient-python';sys.path.insert(0,str(DEPS));import wasmtime as wt


class Stop(Exception):pass


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('cross-engine.py','cross-reference.cjs','guard.cjs'):shutil.copy2(HERE/name,out/'sources'/name)
    staging=out/'inputs';staging.mkdir();shutil.copy2(source/'manifest.json',staging/'manifest.json')
    mf=json.loads((source/'manifest.json').read_text())
    for row in mf['records']:
        folder=staging/row['kind'];folder.mkdir()
        for name in ('target.json','target.wasm','target-O3.wasm'):shutil.copy2(source/row['kind']/name,folder/name)
    try:
        cmd=['node',str(HERE/'cross-reference.cjs'),str(staging),str(out/'reference.json')];r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (out/'node-run.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        cases=json.loads((out/'reference.json').read_text());engine=wt.Engine();checks=0;start=time.perf_counter()
        groups={}
        for case in cases:groups.setdefault((case['kind'],case['file'],case['mode']),[]).append(case)
        for (kind,file,mode),items in groups.items():
            env=json.loads((staging/kind/'target.json').read_text());module=wt.Module(engine,(staging/kind/file).read_bytes());store=wt.Store(engine)
            node=depth=credit=remaining=events=0;ledger=[];started=False
            def adjust(target):
                nonlocal credit,remaining
                assert isinstance(target,int) and target>=0
                delta=target-credit;ledger.append(['reserve',target,delta])
                if delta>remaining:raise Stop()
                remaining-=delta;credit=target
            def bound():return env['whole'] if mode=='whole' else env['depthBounds'][depth] if mode=='depth' else env['nodes'][node]['bound']
            def mark(i,v):
                nonlocal node,depth,events,started
                if i==-2147483648:
                    assert not started;started=True;adjust(bound());return
                assert started;ledger.append(['event',i,v]);events+=1;depth+=1;node=env['nodes'][node]['next'][str(i)+','+str(v)];adjust(bound())
            fn=wt.Func(store,module.imports[0].type,mark);inst=wt.Instance(store,module,[fn]);run=inst.exports(store)['run']
            try:
                for case in items:
                    node=depth=credit=events=0;remaining=case['budget'];ledger=[];started=False;status='ok';value=None
                    try:
                        value=run(store,case['secret'],case['x'])&0xffffffff;ledger.append(['return',value])
                        if mode=='observer':adjust(env['nodes'][node]['terminalBound'])
                    except Stop:status='budget'
                    actual={'status':status,'value':value,'credit':credit,'remaining':remaining,'events':events,'ledger':ledger}
                    assert actual==case['expected'],(kind,file,mode,case['secret'],case['budget'],actual,case['expected']);checks+=1
            finally:store.close()
        report={'wasmtimePython':importlib.metadata.version('wasmtime'),'checks':checks,'groups':len(groups),'seconds':time.perf_counter()-start,'libraryHashes':{str(x.relative_to(DEPS)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (DEPS/'wasmtime').rglob('*.dll')},'limitation':'Finite boundary budgets, 16 secret classes, two payload values. Checks agreement with V8 guard transcripts, not mathematical equivalence or physical timing noninterference.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();main(a.source.resolve(),a.output.resolve())
