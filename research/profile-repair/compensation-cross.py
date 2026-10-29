"""Actual Wasmtime default/DET execution of the native adaptive modules."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import shutil
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'compensation-cross.py')
    request=json.loads((source/'results.json').read_text(encoding='utf8'));rng=random.Random(2026102428)
    tables=[bytes(range(256)),bytes(reversed(range(256))),bytes(256),bytes([255])*256]+[bytes(rng.randrange(256) for _ in range(256)) for _ in range(20)]
    rows=[];calls=0;checked=0;traps=0;start=time.perf_counter()
    try:
        for deterministic in (False,True):
            cfg=wt.Config();cfg.wasm_relaxed_simd=True;cfg.wasm_relaxed_simd_deterministic=deterministic;engine=wt.Engine(cfg)
            for item in request['rows']:
                if item['profile'] is not None:continue
                path=source/'wasm'/item['optimized'];store=wt.Store(engine);e=wt.Instance(store,wt.Module(engine,path.read_bytes()),[]).exports(store);memory=e['memory'];profiles=[]
                for table in tables:
                    data=bytearray([0xa5])*262144;data[:256]=table;data[1024:66560]=bytes(range(256))*256;memory.write(store,data)
                    profiles.append(e['init'](store));after_init=memory.read(store)
                    assert after_init[:512]==data[:512] and after_init[768:]==data[768:]
                    for n in (16,256,65536):
                        before=memory.read(store);e['run'](store,n);after=memory.read(store)
                        assert after[131072:131072+n]==bytes(table[v] for v in before[1024:1024+n])
                        assert after[:131072]==before[:131072] and after[131072+n:]==before[131072+n:]
                        calls+=1;checked+=n
                for n in (-1,1,65537):
                    before=memory.read(store)
                    try:e['run'](store,n)
                    except wt.Trap:traps+=1
                    else:raise AssertionError('missing length trap')
                    assert memory.read(store)==before
                if deterministic:assert set(profiles)=={0}
                rows.append({'mode':item['mode'],'deterministic':deterministic,'profiles':sorted(set(profiles)),'calls':len(tables)*3,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        result={'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'calls':calls,'outputBytesChecked':checked,'traps':traps,'seconds':time.perf_counter()-start,'seed':2026102428,'sourceManifestSHA256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),'note':'Same CPU, actual runtime DET flag. Neither explicit R0 opcode emulation nor an AArch64 machine.'}
        (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    finally:(out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
