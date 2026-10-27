import argparse,json,random,shutil,subprocess
from pathlib import Path
import prototype as p

def run(main,out):
    main=Path(main).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    m=json.loads((main/'manifest.json').read_text(encoding='utf-8'));jobs=[]
    for t in m['targets']:
        if t['opt']!='O3' or t['mode']=='bad':continue
        mod=p.q.read(main/t['file'])
        wrapper=p.q.w.parse('''(module (func (export "bench") (param i32) (result i32) (local i32)
         (block (loop (br_if 1 (i32.ge_u (local.get 1) (local.get 0)))
           (call 0 (i32.const -1)) (local.set 1 (i32.add (local.get 1) (i32.const 1))) (br 0))) (call 1)))''')[1]
        mod.append(wrapper);dst=out/(Path(t['file']).stem+'.bench.wasm');p.q.compile(p.q.w.emit(mod),dst)
        for rep in range(3):jobs.append(dict(name=t['name'],seed=t['seed'],mode=t['mode'],rep=rep,file=dst.name,input_sha256=t['sha256']))
    random.Random(211075).shuffle(jobs);rows=[]
    for job in jobs:
        result=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])],capture_output=True,text=True,timeout=60)
        if result.returncode:raise RuntimeError(result.stderr)
        rows.append(dict(job,measurement=json.loads(result.stdout)));p.q.save(out/'runtime.json',rows)
    for name in {r['name'] for r in rows}:
        assert len({(r['measurement']['initial'],r['measurement']['verification']) for r in rows if r['name']==name})==1
    for f in ('prototype.py','performance.py','bench.cjs'):shutil.copy2(Path(__file__).with_name(f),out/('source-'+f))
    p.q.save(out/'protocol.json',dict(processes=len(rows),order_seed=211075,flags=['--no-liftoff','--no-wasm-lazy-compilation'],
       linear_memory_bytes=65536,affinity='uncontrolled',frequency='uncontrolled',wrapper_after_O3=True,
       pins={str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()}))
    print(json.dumps({'processes':len(rows),'output':str(out)}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
