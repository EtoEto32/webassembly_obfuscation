import argparse,json,random,shutil,statistics,subprocess
from pathlib import Path
import prototype as p

def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((main/'manifest.json').read_text());jobs=[]
    for t in manifest['targets']:
        if t['opt']!='O3' or t['mode']=='bad' or (t['mode']=='recovered' and t['origin_mode']!='plain'):continue
        mod=p.q.read(main/t['file'])
        wrapper=p.q.w.parse('''(module (func (export "bench") (param i32) (result i64) (local i64 i64 i64) (local i32)
        (local.set 1 (i64.const 12345)) (local.set 2 (i64.const 54321))
        (block (loop (br_if 1 (i32.ge_u (local.get 4) (local.get 0)))
        (local.set 1 (i64.add (i64.mul (local.get 1) (i64.const 6364136223846793005)) (i64.const 1442695040888963407)))
        (local.set 2 (i64.xor (local.get 2) (i64.rotl (local.get 1) (i64.const 29))))
        (local.set 3 (i64.xor (local.get 3) (call 0 (local.get 1) (local.get 2))))
        (local.set 4 (i32.add (local.get 4) (i32.const 1))) (br 0))) (local.get 3)))''')[1]
        mod.append(wrapper);dst=out/(Path(t['file']).stem+'.bench.wasm');p.q.compile(p.q.w.emit(mod),dst)
        for rep in range(3):jobs.append(dict(name=t['name'],mode=t['mode'],rep=rep,file=dst.name,input_sha256=t['sha256']))
    random.Random(221024).shuffle(jobs);rows=[]
    for job in jobs:
        result=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])],capture_output=True,text=True,timeout=60)
        if result.returncode:raise RuntimeError(result.stderr)
        rows.append(dict(job,measurement=json.loads(result.stdout)));p.q.save(out/'runtime.json',rows)
    summary=[]
    for name in manifest['fixtures']:
        assert len({r['measurement']['verification'] for r in rows if r['name']==name})==1
        entry=dict(name=name,modes={})
        for mode in ('plain','native8','canonical','zero','bucket','recovered'):
            vals=[r['measurement']['medianNs'] for r in rows if r['name']==name and r['mode']==mode]
            entry['modes'][mode]=dict(median=statistics.median(vals),range=[min(vals),max(vals)])
        summary.append(entry)
    for name in ('prototype.py','performance.py','bench.cjs'):shutil.copy2(Path(__file__).with_name(name),out/('source-'+name))
    p.q.save(out/'summary.json',dict(rows=summary,processes=len(rows),flags=['--no-liftoff','--no-wasm-lazy-compilation'],affinity='uncontrolled',frequency='uncontrolled',loop='Common LCG64/xor-rotate/checksum wrapper appended after O3; no further optimization'))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(summary))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
