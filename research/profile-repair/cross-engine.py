"""Wasmtime native/default and deterministic settings; shared fixed fixtures."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import sys
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'cross-engine.py')
    request=json.loads((source/'request.json').read_text());reference=json.loads((source/'node.json').read_text());refs={r['name']:r['results'] for r in reference['rows']};rows=[];checks=0
    try:
        for deterministic in (False,True):
            cfg=wt.Config();cfg.wasm_relaxed_simd=True;cfg.wasm_relaxed_simd_deterministic=deterministic;engine=wt.Engine(cfg)
            count=0;start=time.perf_counter()
            for row in request['rows']:
                for file in row['files']:
                    store=wt.Store(engine);module=wt.Module(engine,(source/file).read_bytes());run=wt.Instance(store,module,[]).exports(store)['run']
                    values=[run(store,x,y)&0xffffffff for x,y in request['inputs']]
                    if '-original.' in file:
                        allowed=[refs[row['name']][file.replace('.wasm','-profile'+str(i)+'.wasm')] for i in (0,1)]
                        assert values==allowed[0] if deterministic else values in allowed,file
                    else:assert values==refs[row['name']][file],file
                    count+=len(values)
            rows.append({'deterministic':deterministic,'valueChecks':count,'elapsedSeconds':time.perf_counter()-start});checks+=count
        report={'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'valueChecks':checks,'sourceManifestSha256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),'limitation':'Same CPU; default setting and DET option are not two different hardware architectures. No timing comparison between Python and Node.'}
        (out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
    finally:
        (out/'sha256.json').write_text(json.dumps({str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='sha256.json'},indent=2),encoding='utf8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args();main(args.source.resolve(),args.output.resolve())
