"""Identical Wasm-internal loop for every O3 original/transformed/recovered kernel."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import prototype as p
from run import save,command

HERE=Path(__file__).resolve().parent
HARNESS='''(func (export "bench") (param i32 i32) (result i32) (local i32 i32 i32)
 (local.set 2 (local.get 0))
 (local.set 3 (i32.xor (local.get 0) (i32.const 2654435769)))
 (block (loop
  (br_if 1 (i32.eqz (local.get 1)))
  (local.set 2 (i32.add (local.get 2) (i32.const 71717)))
  (local.set 3 (i32.add (local.get 3) (i32.const 13331)))
  (local.set 4 (i32.add (i32.rotl (local.get 4) (i32.const 5)) (call 0 (local.get 2) (local.get 3))))
  (local.set 1 (i32.sub (local.get 1) (i32.const 1)))
  (br 0))) (local.get 4))'''


def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);src=a.output/'sources';src.mkdir();hashes={}
    for path in [HERE/'measure.py',HERE/'batch.cjs']:
        shutil.copyfile(path,src/path.name);hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest=json.loads((a.input/'manifest.json').read_text());files=[]
    for row in manifest['files']:
        if row['opt']!='O3':continue
        mod=p.read(a.input/row['path']);mod.append(p.w.parse('(module '+HARNESS+')')[1]);p.compile_wat(p.emit(mod),a.output/row['path']);files.append(row)
    save(a.output/'manifest.json',dict(files=files,original_directory=str(a.input),source_sha256=hashes))
    save(a.output/'correctness.json',command(['node',HERE/'batch.cjs',a.output,'check']))
    tasks=[(row,i) for row in files for i in range(3)];random.Random(30219).shuffle(tasks);bench=[]
    for count,(row,i) in enumerate(tasks):
        bench.append(dict(row,repeat=i,**command(['node',HERE/'batch.cjs',a.output/row['path']])))
        if count%25==0:print('batch '+str(count),flush=True)
    save(a.output/'benchmark.json',bench);summary=[]
    for row in files:
        b=[x for x in bench if x['path']==row['path']];values=[x['median_ns'] for x in b];data=(a.output/row['path']).read_bytes()
        summary.append(dict(row,median_ns=statistics.median(values),range_ns=[min(values),max(values)],median_rss_KiB=statistics.median(x['maxRSS_KiB'] for x in b),harness_bytes=len(data),harness_sha256=hashlib.sha256(data).hexdigest()))
    save(a.output/'summary.json',summary);print(json.dumps(dict(harnesses=len(files),fresh_processes=len(bench))))


if __name__=='__main__':main()
