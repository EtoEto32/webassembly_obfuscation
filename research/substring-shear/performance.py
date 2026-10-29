import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import prototype as p


def pack(s):return (sum(v<<(2*i) for i,v in enumerate(s[:16])),sum(v<<(2*i) for i,v in enumerate(s[16:])))


def inputs(name,n):
    if name=='dyck':return [[i%2 for i in range(n)],[0]*(n//2)+[1]*(n//2)]
    if name=='palindrome':return [[0]*n,[1]*n]
    return [[0 if i%2==0 else 1 for i in range(n)],[0 if i%2==0 else 2 for i in range(n)]]


def wrapper(src,name,n,dst):
    m=p.q.read(src);run=next(e[2][1] for e in m[1:] if e[:2]==['export','"run"'])
    a,b=map(pack,inputs(name,n));choose=lambda i:f'(select (i32.const {a[i]}) (i32.const {b[i]}) (i32.and (local.get 1) (i32.const 1)))'
    text=f'''(func (export "bench") (param i32 i32) (result i32) (local i32)
      (block $done (loop $loop
        (br_if $done (i32.eqz (local.get 0)))
        (local.set 1 (i32.add (i32.mul (local.get 1) (i32.const 1664525)) (i32.const 1013904223)))
        (local.set 2 (i32.add (i32.mul (local.get 2) (i32.const 33)) (call {run} {choose(0)} {choose(1)} (i32.const {n}))))
        (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br $loop))) (local.get 2))'''
    m.append(p.q.w.parse('(module '+text+')')[1]);p.q.compile(p.q.w.emit(m),dst)


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);targets=[]
    for name in ('dyck','palindrome','expression'):
        for mode,key in [('plain','plain'),('linear','linear-257'),('nonlinear','nonlinear-257'),('recovered','nonlinear-257')]:
            src=base/(name+'-'+key+'-O3'+('-recovered' if mode=='recovered' else '')+'.wasm')
            if mode=='recovered':
                opt=out/(name+'-recovered-O3.wasm');p.q.w.tool('wasm-opt',[src,'--enable-bulk-memory','-O3','-o',opt]);src=opt
            grammar=p.read(src);memory=p.q.read(src);pages=int(next(e[1] for e in memory[1:] if e[0]=='memory'))
            for raw_n in (8,16,32):
                n=raw_n-1 if name=='expression' else raw_n
                dst=out/(name+'-'+mode+'-n%d.wasm'%n);wrapper(src,name,n,dst)
                targets.append(dict(name=name,mode=mode,n=n,file=dst.name,core_bytes=src.stat().st_size,memory_bytes=pages*65536,states=grammar['n'],rules=len(grammar['rules'])))
    p.q.save(out/'manifest.json',targets)
    # Same-count checks across modes before timed execution.
    js="const fs=require('fs');const es=process.argv.slice(1).map(f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports);let rows=[];for(const n of [0,1,2,31,128]){let r=es.map(e=>e.bench(n,0x41b3917)>>>0);if(new Set(r).size!==1)throw Error('checksum');rows.push({count:n,checksum:r[0]});}console.log(JSON.stringify(rows));"
    checks=[]
    for name in ('dyck','palindrome','expression'):
        for n in sorted({x['n'] for x in targets if x['name']==name}):
            paths=[str(out/x['file']) for x in targets if x['name']==name and x['n']==n]
            checks.append(dict(name=name,n=n,checks=json.loads(subprocess.check_output(['node','-e',js,*paths],text=True))))
    p.q.save(out/'wrapper-checks.json',checks)
    schedule=[(i,j) for i in range(len(targets)) for j in range(3)];random.Random(20261023).shuffle(schedule);rows=[]
    for i,rep in schedule:
        target=targets[i];r=subprocess.run(['node','--no-liftoff','--no-wasm-lazy-compilation',str(p.HERE/'bench.cjs'),str(out/target['file'])],capture_output=True,text=True,timeout=60)
        label=Path(target['file']).stem+'-p%d'%rep;(out/(label+'.stdout.txt')).write_text(r.stdout);(out/(label+'.stderr.txt')).write_text(r.stderr)
        if r.returncode:raise RuntimeError(r.stderr)
        rows.append({**target,'rep':rep,**json.loads(r.stdout)});p.q.save(out/'raw.json',rows)
        if len(rows)%12==0:print(json.dumps(dict(done=len(rows),total=len(schedule))),flush=True)
    summary=[]
    for target in targets:
        rs=[r for r in rows if r['file']==target['file']];med=[statistics.median(r['ns_per_call']) for r in rs]
        summary.append({**target,'median_ns':statistics.median(med),'process_medians_ns':med,'rss_kib':[r['max_rss_kib'] for r in rs]})
    p.q.save(out/'summary.json',dict(targets=summary,processes=len(rows),batches=7*len(rows),batches_under_10ms=sum(b['ms']<10 for r in rows for b in r['batches'])))


if __name__=='__main__':main(*sys.argv[1:])
