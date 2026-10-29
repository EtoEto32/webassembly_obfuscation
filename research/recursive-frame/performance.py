import argparse,json,random,shutil,statistics,subprocess
from pathlib import Path
import prototype as p
import recover
def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    jobs=[];binaries=[];analysis=[];protocol=dict(repetitions=3,warmup_calls=16384,batches=9,target_batch_ms=10,max_batch_calls=1<<20,depths=[8,31],flags=['--no-liftoff','--no-wasm-lazy-compilation'],affinity='uncontrolled',frequency='uncontrolled',notes='Common Wasm input-update/checksum loop appended after O3; recovered core also receives O3. No further wrapper optimization. Node maxRSS includes runtime and JIT, not isolated Wasm stack.')
    p.save(out/'protocol.json',protocol)
    for name in ('wide','small','edge'):
        for mode in ('plain','fixed','dynamic','recovered'):
            src=main/(name+'.'+mode+'.O3.wasm') if mode!='recovered' else main/(name+'.dynamic.O3.recovered.wasm')
            if mode=='recovered':
                dst=out/(name+'.recovered.O3.wasm');p.tool('wasm-opt',[src,'-O3','-o',dst]);src=dst
            binaries.append(dict(name=name,mode=mode,bytes=src.stat().st_size,sha256=p.digest(src),linear_memory_bytes=0))
            for depth in (8,31):
                m=p.read(src);wrapper=p.sx.parse(f'''(module (func (export "bench") (param i32) (result i64) (local i32 i32 i32) (local i64)
                (local.set 1 (i32.const 12345)) (local.set 2 (i32.const 54321))
                (block (loop (br_if 1 (i32.ge_u (local.get 3) (local.get 0)))
                (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
                (local.set 2 (i32.xor (i32.rotl (local.get 2) (i32.const 13)) (local.get 1)))
                (local.set 4 (i64.xor (local.get 4) (call 1 (i32.const {depth}) (local.get 1) (local.get 2))))
                (local.set 3 (i32.add (local.get 3) (i32.const 1))) (br 0))) (local.get 4)))''')[1]
                m.append(wrapper);dst=out/f'{name}.{mode}.{depth}.bench.wasm';p.compile(p.sx.emit(m),dst)
                for rep in range(3):jobs.append(dict(name=name,mode=mode,depth=depth,rep=rep,file=dst.name))
    random.Random(221032).shuffle(jobs);rows=[]
    for job in jobs:
        r=subprocess.run(['node',*protocol['flags'],str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])],capture_output=True,text=True,timeout=60)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append(dict(job,measurement=json.loads(r.stdout)));p.save(out/'runtime.json',rows)
    summary=[]
    for name in ('wide','small','edge'):
        for depth in (8,31):
            selected=[r for r in rows if r['name']==name and r['depth']==depth]
            assert len({r['measurement']['verification'] for r in selected})==1
            modes={}
            for mode in ('plain','fixed','dynamic','recovered'):
                vals=[r['measurement']['medianNs'] for r in selected if r['mode']==mode];modes[mode]=dict(median=statistics.median(vals),range=[min(vals),max(vals)])
            summary.append(dict(name=name,depth=depth,modes=modes))
    # Run only after runtime processes have ended. Include I/O separately.
    for name in ('wide','small','edge'):
        for mode in ('plain','fixed','dynamic'):
            for opt in ('raw','O3'):
                src=main/f'{name}.{mode}.{opt}.wasm';samples=[]
                for _ in range(11):_,stats=recover.analyse(src);samples.append(stats)
                analysis.append(dict(name=name,mode=mode,opt=opt,read_median_ms=statistics.median(s['read_validate_ms'] for s in samples),summary_median_ms=statistics.median(s['summary_ms'] for s in samples),samples=samples))
    p.save(out/'analysis.json',analysis);p.save(out/'summary.json',dict(rows=summary,binaries=binaries,processes=len(rows),short_batches=sum(b['ns']<10000000 for r in rows for b in r['measurement']['batches'])))
    p.save(out/'commands.json',p.LOG)
    for name in ('prototype.py','recover.py','performance.py','bench.cjs'):shutil.copy2(Path(__file__).with_name(name),out/('source-'+name))
    p.save(out/'pins.json',{str(f.relative_to(out)):p.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(summary))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
