import argparse,json,random,statistics,subprocess,shutil
from pathlib import Path
import prototype as q
from run import save
p=q.p;HERE=Path(__file__).resolve().parent

def bench(src,dst,n):
    m=p.w.parse(p.w.tool('wasm2wat',[src,'--fold-exprs','--enable-all','--no-debug-names']))
    index=next(e[2][1] for e in m[1:] if isinstance(e,list) and e[0]=='export' and e[1]=='"run"')
    args=['(local.get $h)','(local.get $i)','(i32.xor (local.get $h) (i32.const 1431655765))']+['(i32.const 0)']*(n-3)
    f=f'''(func (export "bench") (param $n i32) (result i32) (local $i i32) (local $h i32)
    (local.set $h (i32.const 137))
    (block $exit (loop $next (br_if $exit (i32.ge_u (local.get $i) (local.get $n)))
    (local.set $h (i32.xor (call {index} {' '.join(args)}) (local.get $i)))
    (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $next))) (local.get $h))'''
    m.append(p.w.parse('(module '+f+')')[1]);p.compile(p.w.emit(m),dst)

def main(source,out):
    source=Path(source);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    snap=out/'sources';snap.mkdir()
    for f in HERE.glob('*'):
        if f.suffix in ('.py','.cjs'):shutil.copyfile(f,snap/f.name)
    manifest=json.loads((source/'manifest.json').read_text());tasks=[];checksums={}
    for row in manifest:
        if row['opt']!='O3':continue
        n=3 if row['mode']=='scalar' else 16;src=source/row['file'];dst=out/row['file'];bench(src,dst,n)
        tasks.append(dict(row,kind='local',workers=n,path=str(dst.resolve())))
        if row['mode']=='atomic':
            for workers in (1,2,4):tasks.append(dict(row,kind='workers',workers=workers,path=str(src.resolve())))
    jobs=[dict(x,rep=rep) for rep in range(3) for x in tasks];random.Random(20261019).shuffle(jobs);results=[]
    for i,job in enumerate(jobs):
        r=subprocess.run(['node',str(HERE/'measure.cjs'),job['path'],job['kind'],str(job['workers'])],capture_output=True,text=True,timeout=30)
        if r.returncode:raise RuntimeError(r.stderr)
        value=json.loads(r.stdout);results.append(dict(job,**value));save(out/'measurements.json',results)
        print(i+1,len(jobs),job['file'],job['kind'],flush=True)
    save(out/'summary.json',dict(processes=len(results),seed=20261019,local_warmup=2048,local_iterations=512,worker_warmup=16,worker_iterations=32,repeats=7,fresh_processes_per_condition=3,local_checksums_consistent=all(len({x['checksum'] for x in results if x['kind']=='local' and x['kernel']==k and x['k']==n})==1 for k,n in {(x['kernel'],x['k']) for x in results})))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source');a.add_argument('output');v=a.parse_args();main(v.source,v.output)
