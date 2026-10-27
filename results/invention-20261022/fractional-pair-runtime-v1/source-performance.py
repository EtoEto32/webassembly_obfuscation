import argparse,json,random,shutil,statistics,subprocess
from pathlib import Path
import prototype as p
def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False);jobs=[];binary=[]
    for name in ('pair','chain','euclid'):
        for mode in ('plain','qsub','zero','fraction','recovered'):
            src=main/(name+'.'+mode+'.O3.wasm') if mode!='recovered' else main/(name+'.fraction.O3.recovered.wasm')
            if mode=='recovered':
                dst=out/(name+'.recovered.O3.wasm');p.q.tool('wasm-opt',[src,'-O3','-o',dst]);src=dst
            binary.append(dict(name=name,mode=mode,bytes=src.stat().st_size,sha256=p.q.digest(src),linear_memory_bytes=0))
            for dist in ('full','small'):
                divisor='(i32.add (i32.shr_u (local.get 2) (i32.const 1)) (i32.const 1))' if dist=='full' else '(i32.add (i32.and (local.get 2) (i32.const 1023)) (i32.const 1))'
                mod=p.q.read(src);wrapper=p.q.w.parse(f'''(module (func (export "bench") (param i32) (result i64) (local i32 i32 i32) (local i64)
                (local.set 1 (i32.const 12345)) (local.set 2 (i32.const 54321))
                (block (loop (br_if 1 (i32.ge_u (local.get 3) (local.get 0)))
                (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
                (local.set 2 (i32.xor (i32.rotl (local.get 2) (i32.const 13)) (local.get 1)))
                (local.set 4 (i64.xor (local.get 4) (call 0 (local.get 1) {divisor})))
                (local.set 3 (i32.add (local.get 3) (i32.const 1))) (br 0))) (local.get 4)))''')[1]
                mod.append(wrapper);dst=out/(name+'.'+mode+'.'+dist+'.bench.wasm');p.q.compile(p.q.w.emit(mod),dst)
                for rep in range(3):jobs.append(dict(name=name,mode=mode,dist=dist,rep=rep,file=dst.name))
    random.Random(221029).shuffle(jobs);rows=[]
    for job in jobs:
        result=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])],capture_output=True,text=True,timeout=60)
        if result.returncode:raise RuntimeError(result.stderr)
        rows.append(dict(job,measurement=json.loads(result.stdout)));p.q.save(out/'runtime.json',rows)
    summary=[]
    for name in ('pair','chain','euclid'):
        for dist in ('full','small'):
            current=[r for r in rows if r['name']==name and r['dist']==dist]
            assert len({r['measurement']['verification'] for r in current})==1
            modes={}
            for mode in ('plain','qsub','zero','fraction','recovered'):
                vals=[r['measurement']['medianNs'] for r in current if r['mode']==mode]
                modes[mode]=dict(median=statistics.median(vals),range=[min(vals),max(vals)])
            summary.append(dict(name=name,distribution=dist,modes=modes))
    p.q.save(out/'summary.json',dict(rows=summary,binaries=binary,processes=len(rows),flags=['--no-liftoff','--no-wasm-lazy-compilation'],warmup=65536,batches=9,affinity='uncontrolled',frequency='uncontrolled',wrapper='Same input-update/checksum loop appended after O3; no further optimization. Recovered binaries receive O3 before wrapping.'))
    for name in ('prototype.py','performance.py','bench.cjs'):shutil.copy2(Path(__file__).with_name(name),out/('source-'+name))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(summary))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
