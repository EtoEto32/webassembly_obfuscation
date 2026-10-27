import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import prototype as p


def wrapper(src,plan,dst):
    m=p.q.read(src);run=next(e[2][1] for e in m[1:] if e[:2]==['export','"run"']);args=[None]*(3*len(plan)+1)
    for step,(d,s,l) in enumerate(plan):
        args[d]=f'(i32.and (i32.xor (local.get 1) (i32.const {step*7349})) (i32.const 32767))'
        args[s]=f'(i32.and (i32.xor (i32.rotr (local.get 1) (i32.const 11)) (i32.const {step*11971})) (i32.const 32767))'
        args[l]='(i32.const 16384)'
    args[-1]='(i32.and (local.get 1) (i32.const 65535))'
    text=f'''(func (export "bench") (param i32 i32) (result i32) (local i32)
      (block $done (loop $loop (br_if $done (i32.eqz (local.get 0)))
        (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
        (local.set 2 (i32.add (i32.mul (local.get 2) (i32.const 33)) (call {run} {' '.join(args)})))
        (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br $loop))) (local.get 2))'''
    m.append(p.q.w.parse('(module '+text+')')[1]);p.q.compile(p.q.w.emit(m),dst)


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    cases=json.loads((base/'cases.json').read_text());targets=[]
    for case in cases:
        if not case['name'].endswith('v0'):continue
        name=case['name']
        for mode in ('plain','pullback','recovered'):
            src=base/(name+'-'+('pullback-O3-recovered' if mode=='recovered' else mode+'-O3')+'.wasm')
            if mode=='recovered':
                opt=out/(name+'-recovered-O3.wasm');p.q.w.tool('wasm-opt',[src,'--enable-bulk-memory','-O3','-o',opt]);src=opt
            dst=out/(name+'-'+mode+'-bench.wasm');wrapper(src,case['plan'],dst)
            targets.append(dict(name=name,mode=mode,copies=len(case['plan']),file=dst.name,core_bytes=src.stat().st_size,memory_bytes=65536))
    js="const fs=require('fs');const es=process.argv.slice(1).map(f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports);let rows=[];for(const n of [0,1,2,31,1024]){let r=es.map(e=>e.bench(n,0x41b3917)>>>0);if(new Set(r).size!==1)throw Error('checksum');rows.push({count:n,checksum:r[0]});}console.log(JSON.stringify(rows));"
    checks=[]
    for name in sorted({x['name'] for x in targets}):
        paths=[str(out/x['file']) for x in targets if x['name']==name];checks.append(dict(name=name,checks=json.loads(subprocess.check_output(['node','-e',js,*paths],text=True))))
    p.q.save(out/'wrapper-checks.json',checks)
    rows=[];schedule=[(i,j) for i in range(len(targets)) for j in range(3)];random.Random(20261023).shuffle(schedule)
    for i,rep in schedule:
        t=targets[i];r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.HERE.parent/'span-mask/bench.cjs'),str(out/t['file'])],capture_output=True,text=True,timeout=60)
        label=Path(t['file']).stem+'-p%d'%rep;(out/(label+'.stdout.txt')).write_text(r.stdout);(out/(label+'.stderr.txt')).write_text(r.stderr)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append({**t,'rep':rep,**json.loads(r.stdout)});p.q.save(out/'raw.json',rows)
    summary=[]
    for t in targets:
        rs=[r for r in rows if r['file']==t['file']];med=[statistics.median(r['ns_per_call']) for r in rs]
        summary.append({**t,'median_ns':statistics.median(med),'process_medians_ns':med,'rss_kib':[r['max_rss_kib'] for r in rs]})
    p.q.save(out/'summary.json',dict(targets=summary,processes=len(rows),batches=7*len(rows),batches_under_10ms=sum(b['ms']<10 for r in rows for b in r['batches'])))
    print(json.dumps(dict(processes=len(rows),batches=7*len(rows))))


if __name__=='__main__':main(*sys.argv[1:])
