import argparse
import json
import random
import shutil
import subprocess
from pathlib import Path
import prototype as p


def run(main,out):
    main=Path(main).resolve(); out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    m=json.loads((main/'manifest.json').read_text(encoding='utf-8')); jobs=[]
    for target in m['targets']:
        if target['opt']!='O3':continue
        variants=[(target['mode'],target['file'])]
        if target['mode']=='jet':variants.append(('recovered',target['recovered']))
        for mode,file in variants:
            mod=p.q.read(main/file)
            wrapper=p.q.w.parse('''(module (func (export "bench") (param i32 i32) (result i32) (local i32 i32 i32 i32)
              (local.set 4 (local.get 1))
              (local.set 5 (i32.xor (local.get 1) (i32.const 2654435769)))
              (block (loop
                (br_if 1 (i32.ge_u (local.get 2) (local.get 0)))
                (local.set 4 (i32.add (i32.mul (local.get 4) (i32.const 1664525)) (i32.const 1013904223)))
                (local.set 5 (i32.rotl (i32.xor (local.get 5) (local.get 4)) (i32.const 5)))
                (local.set 3 (i32.xor (local.get 3) (call 0 (local.get 4) (local.get 5))))
                (local.set 2 (i32.add (local.get 2) (i32.const 1))) (br 0))) (local.get 3)))''')[1]
            mod.append(wrapper); dest=out/(target['name']+'.'+mode+'.wasm');p.q.compile(p.q.w.emit(mod),dest)
            for rep in range(3):jobs.append(dict(name=target['name'],mode=mode,rep=rep,file=dest.name,source_sha256=p.q.digest(main/file)))
    random.Random(2026102131).shuffle(jobs)
    rows=[]
    for job in jobs:
        r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])],capture_output=True,text=True,timeout=60)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append(dict(job,measurement=json.loads(r.stdout)))
        p.q.save(out/'runtime.json',rows)
    for name in {r['name'] for r in rows}:
        assert len({r['measurement']['verification'] for r in rows if r['name']==name})==1
    for f in ('prototype.py','performance.py','bench.cjs'):shutil.copy2(Path(__file__).with_name(f),out/('source-'+f))
    p.q.save(out/'protocol.json',dict(order_seed=2026102131,jobs=jobs,flags=['--no-liftoff','--no-wasm-lazy-compilation'],
       process_count=len(rows),affinity='uncontrolled',frequency='uncontrolled',linear_memory_bytes=0,
       wrapper='Added after wasm-opt O3; no further Binaryen optimization.',
       pins={str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()}))
    print(json.dumps({'processes':len(rows),'output':str(out)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
