import argparse,json,random,statistics,subprocess
from pathlib import Path
import prototype as p
import run as runner

def run(main,output):
    main,out=Path(main).resolve(),Path(output).resolve();out.mkdir(parents=True,exist_ok=False);jobs=[];binaries=[]
    flags=['--no-liftoff','--no-wasm-lazy-compilation']
    for name in runner.NAMES:
        for mode in ('plain','fixed','full','transport','recovered'):
            src=main/f'{name}.{mode}.O3.wasm'
            if mode=='recovered':
                src=out/f'{name}.recovered.O3.wasm';p.q.tool('wasm-opt',[main/f'{name}.transport.O3.recovered.wasm','--enable-simd','-O3','-o',src])
            m=p.q.read(src);idx=next(x[2][1] for x in m[1:] if x[0]=='export' and x[1]=='"run"')
            binaries.append(dict(name=name,mode=mode,bytes=src.stat().st_size,linear_memory_bytes=65536,sha256=p.q.digest(src)))
            m.append(['export','"__physical"',['memory','0']])
            wrapper=f'''(module (func (export "__bench") (param $limit i32) (result i32) (local $i i32) (local $x i32) (local $sum i32)
            (local.set $x (i32.const 12345))
            (block $done (loop $next (br_if $done (i32.ge_u (local.get $i) (local.get $limit)))
              (local.set $x (i32.add (i32.mul (local.get $x) (i32.const 1664525)) (i32.const 1013904223)))
              (local.set $sum (i32.xor (local.get $sum) (call {idx}
                (i32.shl (i32.and (local.get $i) (i32.const 15)) (i32.const 4))
                (local.get $x) (i32.add (i32.and (local.get $i) (i32.const 7)) (i32.const 1)))))
              (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $next))) (local.get $sum)))'''
            m.append(p.sx.parse(wrapper)[1]);dst=out/f'{name}.{mode}.bench.wasm';p.q.compile(p.sx.emit(m),dst)
            for rep in range(3):jobs.append(dict(name=name,mode=mode,rep=rep,file=dst.name))
    random.Random(221124).shuffle(jobs);rows=[]
    p.q.save(out/'protocol.json',dict(processes=45,batches_per_process=9,warmup=16384,target_ms=10,cap=1<<22,flags=flags,shuffle_seed=221124,memory_reset='Before each timed call, outside timer; state preserved within each call.',cpu_affinity='uncontrolled',frequency='uncontrolled',wrapper='Added after core O3; input loop, 1..8 updates and checksum included.'))
    for job in jobs:
        r=subprocess.run(['node',*flags,str(Path(__file__).with_name('bench.cjs')),str(out/job['file'])],capture_output=True,text=True,timeout=60,check=True)
        rows.append(dict(job,measurement=json.loads(r.stdout)));p.q.save(out/'runtime.json',rows)
    summaries=[]
    for name in runner.NAMES:
        selected=[x for x in rows if x['name']==name];assert len({x['measurement']['verification'] for x in selected})==1
        modes={}
        for mode in ('plain','fixed','full','transport','recovered'):
            values=[x['measurement']['medianNs'] for x in selected if x['mode']==mode];modes[mode]=dict(median=statistics.median(values),range=[min(values),max(values)])
        summaries.append(dict(name=name,modes=modes,transport_over_full=modes['transport']['median']/modes['full']['median'],transport_over_plain=modes['transport']['median']/modes['plain']['median']))
    p.q.save(out/'summary.json',dict(rows=summaries,binaries=binaries,processes=len(rows),batches=sum(len(x['measurement']['batches']) for x in rows),short_batches=sum(b['ns']<1e7 for x in rows for b in x['measurement']['batches'])))
    runner.pin(out);print(json.dumps(summaries))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('main');ap.add_argument('output');a=ap.parse_args();run(a.main,a.output)
