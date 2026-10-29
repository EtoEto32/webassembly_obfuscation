import argparse,json,random,statistics,subprocess
from pathlib import Path
import prototype as p
import attack
import run as runner

def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    flags=['--no-liftoff','--no-wasm-lazy-compilation'];jobs=[];binaries=[]
    bench=p.ROOT/'research/unit-minor/bench.cjs'
    p.save(out/'protocol.json',dict(repetitions=3,batches=9,warmup=16384,target_ms=10,cap=1<<24,flags=flags,affinity='uncontrolled',frequency='uncontrolled',bench=str(bench),bench_sha256=p.digest(bench),notes='Common Wasm wrapper after O3; Node RSS includes runtime/JIT. Analysis measured after runtime.'))
    for name in runner.FIXTURES:
        for mode in ('plain','constant','congruent','rotated','recovered'):
            src=main/f'{name}.{mode}.O3.wasm'
            if mode=='recovered':
                src=out/f'{name}.recovered.O3.wasm';p.tool('wasm-opt',[main/f'{name}.rotated.O3.recovered.wasm','-O3','-o',src])
            m=p.w.read(src);idx=next(x[2][1] for x in m[1:] if x[0]=='export' and x[1]=='"run"')
            binaries.append(dict(name=name,mode=mode,bytes=src.stat().st_size,linear_memory_bytes=0,sha256=p.digest(src)))
            wrapper=f'''(module (func (export "bench") (param $limit i32) (result i32)
            (local $x i32) (local $y i32) (local $z i32) (local $i i32) (local $sum i32)
            (local.set $x (i32.const 12345)) (local.set $y (i32.const 6789)) (local.set $z (i32.const 1357))
            (block $done (loop $next
            (br_if $done (i32.ge_u (local.get $i) (local.get $limit)))
            (local.set $x (i32.add (i32.mul (local.get $x) (i32.const 1664525)) (i32.const 1013904223)))
            (local.set $y (i32.xor (i32.rotl (local.get $y) (i32.const 13)) (local.get $x)))
            (local.set $z (i32.add (local.get $z) (local.get $y)))
            (local.set $sum (i32.xor (local.get $sum) (call {idx} (local.get $x) (local.get $y) (local.get $z))))
            (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $next))) (local.get $sum)))'''
            m.append(p.w.sx.parse(wrapper)[1]);dst=out/f'{name}.{mode}.bench.wasm';p.compile_wat(p.w.sx.emit(m),dst)
            for rep in range(3):jobs.append(dict(name=name,mode=mode,rep=rep,file=dst.name))
    random.Random(221051).shuffle(jobs);rows=[]
    for job in jobs:
        r=subprocess.run(['node',*flags,str(bench),str(out/job['file'])],capture_output=True,text=True,timeout=60)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append(dict(job,measurement=json.loads(r.stdout)));p.save(out/'runtime.json',rows)
    summary=[]
    for name in runner.FIXTURES:
        chosen=[x for x in rows if x['name']==name];assert len({x['measurement']['verification'] for x in chosen})==1
        modes={}
        for mode in ('plain','constant','congruent','rotated','recovered'):
            values=[x['measurement']['medianNs'] for x in chosen if x['mode']==mode]
            modes[mode]=dict(median=statistics.median(values),range=[min(values),max(values)])
        summary.append(dict(name=name,modes=modes))
    analyses=[]
    for name in runner.FIXTURES:
        for mode in ('constant','congruent','rotated'):
            for opt in ('raw','O3'):
                samples=[attack.extract(main/f'{name}.{mode}.{opt}.wasm')[1] for _ in range(11)]
                analyses.append(dict(name=name,mode=mode,opt=opt,read_median_ms=statistics.median(x['read_ms'] for x in samples),recovery_median_ms=statistics.median(x['recovery_ms'] for x in samples),samples=samples))
    p.save(out/'analysis.json',analyses);p.save(out/'summary.json',dict(rows=summary,binaries=binaries,processes=len(rows),batches=9*len(rows),short_batches=sum(b['ns']<10000000 for x in rows for b in x['measurement']['batches'])))
    runner.pin(out);print(json.dumps(summary))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
