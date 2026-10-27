"""Compare Wasmtime against the independent JS model also checked in V8."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
DEPS=ROOT/'.tools/import-alias-quotient-python';sys.path.insert(0,str(DEPS))
import wasmtime as wt


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();staging=out/'inputs';staging.mkdir()
    for name in ('cross-engine.py','run.cjs','plan.md','reader-note.md'):shutil.copy2(HERE/name,out/'sources'/name)
    try:
        mf=json.loads((source/'manifest.json').read_text());shutil.copy2(source/'manifest.json',staging/'manifest.json')
        for rec in mf['records']:
            folder=staging/rec['folder'];folder.mkdir()
            for p in (source/rec['folder']).glob('*.wasm'):shutil.copy2(p,folder/p.name)
        cmd=['node',str(HERE/'run.cjs'),str(staging),'--read-only','--trace',str(out/'reference.json')]
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        (out/'node.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf8')
        if r.returncode:raise RuntimeError(r.stderr)
        refs=json.loads((out/'reference.json').read_text());group={}
        for row in refs:group.setdefault((row['fixture'],row['alias']),[]).append(row)
        config=wt.Config();config.wasm_multi_memory=True;engine=wt.Engine(config);cache={};checks=0;memchecks=0;traps=0;instances=0;start=time.perf_counter()
        initial=[bytes((i*17+c*13)&255 for i in range(65536)) for c in range(4)]
        for rec in mf['records']:
          for alias in rec['aliases']:
           p=alias['partition']
           for name,quotient in [('original',False),('original-O3',False),('q'+str(alias['id']),True),('q'+str(alias['id'])+'-O3',True)]:
            file=staging/rec['folder']/(name+'.wasm')
            if file not in cache:cache[file]=wt.Module(engine,file.read_bytes())
            store=wt.Store(engine)
            try:
                memories=[wt.Memory(store,wt.MemoryType(wt.Limits(1,3))) for _ in range(max(p)+1)]
                for c,m in enumerate(memories):m.write(store,initial[c])
                imports=[memories[p[i]] for i in (alias['representatives'] if quotient else range(rec['n']))]
                inst=wt.Instance(store,cache[file],imports);run=inst.exports(store)['run'];instances+=1
                for row in group[(rec['folder'],alias['id'])]:
                    actual={'status':'complete','value':None}
                    try:actual['value']=run(store,*row['args'])&0xffffffff
                    except wt.Trap:actual['status']='trap';traps+=1
                    if actual!=row['expected']:raise AssertionError((rec['folder'],name,p,row['args'],actual,row['expected']))
                    checks+=1
                    for c,m in enumerate(memories):
                        data=m.read(store);actual={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
                        if actual!=row['memories'][c]:raise AssertionError(('memory',rec['folder'],name,p,row['args'],c))
                        memchecks+=1
            finally:store.close()
        dlls={str(p.relative_to(DEPS)):hashlib.sha256(p.read_bytes()).hexdigest() for p in DEPS.rglob('*.dll')}
        report={'wasmtimePython':importlib.metadata.version('wasmtime'),'libraryHashes':dlls,'instances':instances,'checks':checks,'memoryChecks':memchecks,'trapChecks':traps,'seconds':time.perf_counter()-start,
          'reference':'Independent JavaScript fixture model, checked byte-for-byte against V8; Wasmtime compares full-memory SHA-256 and length after every call.',
          'limitation':'SHA-256 comparison here is evidence of matching snapshots, not a proof of equivalence. No Python export-object identity claim.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
