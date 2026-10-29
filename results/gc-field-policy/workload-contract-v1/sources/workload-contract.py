"""Exercise private-value independence and import allowlists in both engines."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from workload import ROOT,HERE,CHECK,w,MODES,producer,consumer,policy,expected


def main(out):
    out.mkdir(parents=True,exist_ok=False);cases=[];rows=[]
    config=w.Config();config.wasm_gc=True;config.wasm_function_references=True;engine=w.Engine(config)
    for mode in MODES:
        libbytes=bytes(w.wat2wasm(producer(mode)));clientbytes=bytes(w.wat2wasm(consumer(mode)))
        (out/f'{mode}-lib.wasm').write_bytes(libbytes);(out/f'{mode}-client.wasm').write_bytes(clientbytes)
        allowed=['refresh']+(['x','y'] if mode=='accessor' else ['view'])
        for n in (1,2,128):
            for secret in (0,77123,-2147483648):
                case=dict(mode=mode,n=n,secret=secret,library=list(libbytes),consumer=list(clientbytes),policy=policy(mode),allowed=allowed)
                p=subprocess.run([str(CHECK),'--stdin'],input=json.dumps(case),capture_output=True,text=True,timeout=60)
                assert p.returncode==0,p.stderr
                assert next(x['accepted'] for x in json.loads(p.stdout)['results'] if x['mode']=='closure')
                store=w.Store(engine);lib=w.Instance(store,w.Module(engine,libbytes),[]);linker=w.Linker(engine)
                for name in allowed:linker.define(store,'lib',name,lib.exports(store)[name])
                client=linker.instantiate(store,w.Module(engine,clientbytes));lib.exports(store)['init'](store,n,secret)
                f=client.exports(store)['run']
                for k in range(12):f(store,n,8,17,123456+k)
                checks=[f(store,n,8,17,123456+k) for k in range(11)]
                assert checks==expected(n,8)
                private=[lib.exports(store)['private-at'](store,i) for i in range(n)]
                assert private==[(i ^ (secret&0xffffffff)) if (i ^ (secret&0xffffffff))<0x80000000 else (i ^ (secret&0xffffffff))-0x100000000 for i in range(n)]
                cases.append(case);rows.append(dict(mode=mode,n=n,secret=secret,checks=checks,private=private))
    bad=bytes(w.wat2wasm('(module (import "lib" "private-at" (func $p (param i32) (result i32))) (func (export "run") (result i32) i32.const 0 call $p))'))
    lib=bytes(w.wat2wasm(producer('shared')));pol=policy('shared')
    checked=subprocess.run([str(CHECK),'--stdin'],input=json.dumps(dict(library=list(lib),consumer=list(bad),policy=pol)),capture_output=True,text=True,timeout=60)
    assert checked.returncode==0
    assert next(x['accepted'] for x in json.loads(checked.stdout)['results'] if x['mode']=='closure')
    store=w.Store(engine);provider=w.Instance(store,w.Module(engine,lib),[]);linker=w.Linker(engine)
    for name in ('refresh','view'):linker.define(store,'lib',name,provider.exports(store)[name])
    try:linker.instantiate(store,w.Module(engine,bad))
    except w.WasmtimeError as e:import_reject=str(e)
    else:raise AssertionError('private-at import was exposed')
    spec=dict(cases=cases,bad=dict(library=list(lib),consumer=list(bad),policy=pol,allowed=['refresh','view']))
    specfile=out/'inputs.json';specfile.write_text(json.dumps(spec))
    p=subprocess.run(['node',str(HERE/'workload-contract.mjs'),str(CHECK),str(specfile)],capture_output=True,text=True,timeout=60)
    (out/'node-command.json').write_text(json.dumps(dict(code=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
    node=json.loads(p.stdout);assert node['rows']==rows;assert node['badImport']=='import-reject'
    (out/'python-rows.json').write_text(json.dumps(rows,indent=2))
    (out/'summary.json').write_text(json.dumps(dict(pairsPerEngine=len(rows),apiChecksPerEngine=len(rows)*11,
        privateValueChecksPerEngine=sum(r['n'] for r in rows),privateDifferentialValues=3,
        badImport=dict(gcPolicyAccepted=True,node=node['badImport'],wasmtime=import_reject)),indent=2))
    sources=out/'sources';sources.mkdir()
    for path in (HERE/'workload-contract.py',HERE/'workload-contract.mjs',HERE/'workload.py',HERE/'loader.mjs',HERE/'checker/src/main.rs'):
        shutil.copyfile(path,sources/path.name)
    (out/'hashes.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2))
    print(json.dumps(dict(pairsPerEngine=len(rows),mismatches=0,badImportRejectedBoth=True)))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
