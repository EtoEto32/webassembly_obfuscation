"""Actual Binaryen generator comparison. Generated guests are NOT executed."""
import argparse,collections,json,random,shutil,subprocess,time
from pathlib import Path
from experiment import wt,ROOT,HERE,CHECKER,dump,digest
def main(out,seeds):
    out.mkdir(parents=True,exist_ok=False);rows=[];records=[]
    opt=ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe'
    fixtures={
        'cycle-array':'(rec (type $a (array (ref $a))))',
        'nullable-array':'(rec (type $a (array (ref null $a))))',
        'scalar-array':'(type $a (array i32))',
        'cycle-struct':'(rec (type $a (struct (field (ref $a)))))',
    }
    for name,types in fixtures.items():
        wat='(module '+types+' (func (export "observe") (param (ref null $a)) (result i32) (i32.const 1)))'
        init=out/(name+'.wasm');init.write_bytes(wt.wat2wasm(wat));(out/(name+'.wat')).write_text(wat)
        for seed in range(seeds):
            rng=random.Random(seed);data=bytes(rng.getrandbits(8) for _ in range(1024));inp=out/('%s-%d.seed'%(name,seed));inp.write_bytes(data);dest=out/('%s-%d.wasm'%(name,seed))
            cmd=[str(opt),str(inp),'-ttf','--initial-fuzz='+str(init),'--fuzz-preserve-imports-exports','--enable-gc','--enable-reference-types','--enable-multivalue','--enable-simd','--disable-custom-descriptors','-o',str(dest)]
            t=time.perf_counter_ns()
            try:
                cp=subprocess.run(cmd,capture_output=True,text=True,timeout=8)
                row=dict(name=name,seed=seed,code=cp.returncode,stdout=cp.stdout,stderr=cp.stderr,ms=(time.perf_counter_ns()-t)/1e6,command=cmd)
                if cp.returncode==0:
                    c=subprocess.run([str(CHECKER),'compare',str(init),'0',str(dest)],capture_output=True,text=True,timeout=8);c.check_returncode();row['comparison']=json.loads(c.stdout)
                    row['status']='ok' if row['comparison']['status']=='compared' else 'checker-rejected'
                else:row['status']='generator-error'
            except subprocess.TimeoutExpired:row=dict(name=name,seed=seed,status='timeout',ms=(time.perf_counter_ns()-t)/1e6,command=cmd)
            rows.append(row)
    summary={name:dict(status=dict(collections.Counter(r['status'] for r in rows if r['name']==name)),with_target_constructor=sum(r.get('comparison',{}).get('constructors',0)>0 for r in rows if r['name']==name),total_target_constructors=sum(r.get('comparison',{}).get('constructors',0) for r in rows if r['name']==name)) for name in fixtures}
    dump(out/'rows.json',rows);dump(out/'summary.json',summary)
    for p in [HERE/'binaryen-probe.py',HERE/'checker/src/main.rs',CHECKER]:shutil.copy2(p,out/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(summary,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--seeds',type=int,default=32);a=ap.parse_args();main(a.out,a.seeds)
