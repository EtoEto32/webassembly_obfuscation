import argparse
import json
import random
import statistics
import subprocess
from pathlib import Path
import prototype as p
import recover
import run as mainrun


def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve(); out.mkdir(parents=True,exist_ok=False)
    protocol=dict(repetitions=3,warmup_calls=1024,batches=9,target_batch_ms=10,max_batch_calls=1<<20,flags=['--no-liftoff','--no-wasm-lazy-compilation'],affinity='uncontrolled',frequency='uncontrolled',notes='Common Wasm wrapper appended after core O3. Node RSS includes runtime and JIT. No secret data supplied to recovery.')
    p.save(out/'protocol.json',protocol); jobs=[]; binaries=[]
    for name in mainrun.FIXTURES:
        for mode in ('plain','unmixed','constant','polynomial','recovered'):
            src=main/f'{name}.{mode}.O3.wasm'
            if mode=='recovered':
                src=out/f'{name}.recovered.O3.wasm'; p.tool('wasm-opt',[main/f'{name}.polynomial.O3.recovered.wasm','-O3','-o',src])
            m=p.read(src); index=next(x[2][1] for x in m[1:] if x[0]=='export' and x[1]=='"run"')
            binaries.append(dict(name=name,mode=mode,bytes=src.stat().st_size,linear_memory_bytes=131072 if mode in ('unmixed','constant','polynomial') else 0,sha256=p.digest(src)))
            wrapper=f'''(module (func (export "bench") (param $limit i32) (result i32)
            (local $x i32) (local $y i32) (local $z i32) (local $i i32) (local $sum i32)
            (local.set $x (i32.const 12345)) (local.set $y (i32.const 6789)) (local.set $z (i32.const 1357))
            (block $done (loop $next
              (br_if $done (i32.ge_u (local.get $i) (local.get $limit)))
              (local.set $x (i32.add (i32.mul (local.get $x) (i32.const 1664525)) (i32.const 1013904223)))
              (local.set $y (i32.xor (i32.rotl (local.get $y) (i32.const 13)) (local.get $x)))
              (local.set $z (i32.add (local.get $z) (local.get $y)))
              (local.set $sum (i32.xor (local.get $sum) (call {index} (local.get $x) (local.get $y) (local.get $z))))
              (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $next))) (local.get $sum)))'''
            m.append(p.sx.parse(wrapper)[1]); dst=out/f'{name}.{mode}.bench.wasm'; p.compile_wat(p.sx.emit(m),dst)
            for rep in range(3): jobs.append(dict(name=name,mode=mode,rep=rep,file=dst.name))
    random.Random(221043).shuffle(jobs); rows=[]
    for job in jobs:
        r=subprocess.run(['node',*protocol['flags'],str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])],capture_output=True,text=True,timeout=60)
        if r.returncode: raise RuntimeError(r.stderr)
        rows.append(dict(job,measurement=json.loads(r.stdout))); p.save(out/'runtime.json',rows)
    summary=[]
    for name in mainrun.FIXTURES:
        chosen=[r for r in rows if r['name']==name]
        assert len({r['measurement']['verification'] for r in chosen})==1
        modes={}
        for mode in ('plain','unmixed','constant','polynomial','recovered'):
            vals=[r['measurement']['medianNs'] for r in chosen if r['mode']==mode]
            modes[mode]=dict(median=statistics.median(vals),range=[min(vals),max(vals)])
        summary.append(dict(name=name,modes=modes))
    accepted=recover.templates(out/'templates'); analyses=[]
    for name in mainrun.FIXTURES:
        for mode in ('unmixed','constant','polynomial'):
            for opt in ('raw','O3'):
                samples=[]
                for _ in range(11):
                    m,read_ms=recover.extract(main/f'{name}.{mode}.{opt}.wasm',accepted)
                    _,stats=recover.determinant(m); stats['read_validate_ms']=read_ms; samples.append(stats)
                analyses.append(dict(name=name,mode=mode,opt=opt,read_median_ms=statistics.median(x['read_validate_ms'] for x in samples),symbolic_median_ms=statistics.median(x['symbolic_ms'] for x in samples),samples=samples))
    p.save(out/'analysis.json',analyses)
    p.save(out/'summary.json',dict(rows=summary,binaries=binaries,processes=len(rows),batches=sum(len(r['measurement']['batches']) for r in rows),short_batches=sum(b['ns']<10000000 for r in rows for b in r['measurement']['batches'])))
    mainrun.pin(out); print(json.dumps(summary))


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('main'); ap.add_argument('output'); a=ap.parse_args(); run(a.main,a.output)
