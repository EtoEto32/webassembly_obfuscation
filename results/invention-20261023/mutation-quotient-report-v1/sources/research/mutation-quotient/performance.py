import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import prototype as p


def wrapper(src,n,dst):
    m=p.q.read(src);exports={e[1].strip('"'):e[2][1] for e in m[1:] if e[0]=='export'}
    text=f'''(func (export "bench") (param i32 i32) (result i32) (local i32)
      (call {exports['reset']})
      (loop $loop
        (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
        (local.set 2 (i32.xor (local.get 2) (call {exports['run']}
          (i32.and (i32.shr_u (local.get 1) (i32.const 24)) (i32.const 3))
          (i32.rem_u (local.get 1) (i32.const {n}))
          (i32.rem_u (i32.shr_u (local.get 1) (i32.const 8)) (i32.const {n})) (local.get 1))))
        (local.set 0 (i32.sub (local.get 0) (i32.const 1)))
        (br_if $loop (local.get 0))) (local.get 2))'''
    m.append(p.q.w.parse('(module '+text+')')[1]);p.q.compile(p.q.w.emit(m),dst)


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);targets=[]
    for n in (4,32,256):
        for mode in ('plain','representative','canonical','recovered'):
            stem='n%d-k257-'%n
            src=base/(stem+('canonical-O3-recovered' if mode=='recovered' else mode+'-O3')+'.wasm')
            if mode=='recovered':
                optimized=out/(stem+'recovered-O3.wasm');p.q.w.tool('wasm-opt',[src,'-O3','-o',optimized]);src=optimized
            dst=out/(stem+mode+'-bench.wasm');wrapper(src,n,dst)
            targets.append(dict(n=n,mode=mode,file=dst.name,core_bytes=src.stat().st_size,linear_memory_bytes=65536))
    schedule=[(i,j) for i in range(len(targets)) for j in range(3)];random.Random(20261023).shuffle(schedule);rows=[]
    for i,rep in schedule:
        t=targets[i];r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.HERE.parent/'span-mask/bench.cjs'),str(out/t['file'])],capture_output=True,text=True,timeout=120)
        label='n%d-%s-%d'%(t['n'],t['mode'],rep);(out/(label+'.stdout.txt')).write_text(r.stdout);(out/(label+'.stderr.txt')).write_text(r.stderr)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append({**t,'rep':rep,**json.loads(r.stdout)});p.q.save(out/'raw.json',rows);print(json.dumps(dict(done=len(rows),label=label)),flush=True)
    summary=[]
    for t in targets:
        rs=[r for r in rows if r['file']==t['file']];med=[statistics.median(r['ns_per_call']) for r in rs]
        summary.append({**t,'median_ns':statistics.median(med),'process_medians_ns':med,'rss_kib':[r['max_rss_kib'] for r in rs]})
    p.q.save(out/'summary.json',dict(targets=summary,processes=len(rows),batches=7*len(rows),batches_under_10ms=sum(b['ms']<10 for r in rows for b in r['batches'])))


if __name__=='__main__':main(sys.argv[1],sys.argv[2])
