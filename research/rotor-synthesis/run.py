import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import prototype as p

FIXTURES={
 'and3':'(i32.and (i32.and (local.get 0) (local.get 1)) (local.get 2))',
 'majority3':'(i32.or (i32.and (local.get 0) (local.get 1)) (i32.or (i32.and (local.get 0) (local.get 2)) (i32.and (local.get 1) (local.get 2))))',
 'mux3':'(i32.or (i32.and (local.get 0) (local.get 1)) (i32.and (i32.xor (local.get 0) (i32.const -1)) (local.get 2)))'}

def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);manifest=[];attacks=[]
    for name,expr in FIXTURES.items():
        raw=out/(name+'-plain.wasm');p.save(f'(module (func (export "run") (param i32 i32 i32) (result i32) {expr}))',raw)
        dest=out/(name+'-rotor.wasm');r=p.transform(raw,dest,d=4,bound=10,cyclic=(name=='and3'))
        (out/(name+'-synthesis.json')).write_text(json.dumps(r,indent=2));print(json.dumps({'name':name,**r}),flush=True)
        if r['status']!='sat':continue
        for mode in ('plain','rotor'):
            src=out/(name+'-'+mode+'.wasm');opt=out/(name+'-'+mode+'-O3.wasm');p.w.tool('wasm-opt',[src,'-O3','--enable-bulk-memory','-o',opt])
            manifest+=[{'name':name,'mode':mode,'optimization':o,'file':f.name,'bytes':f.stat().st_size,'memory_bytes':65536 if mode=='rotor' else 0} for o,f in [('raw',src),('O3',opt)]]
        for opt in ('raw','O3'):
            src=out/(name+'-rotor'+('-O3' if opt=='O3' else '')+'.wasm');start=time.perf_counter();g=p.read(src);read_ms=1000*(time.perf_counter()-start)
            t,a=p.recover(g);start=time.perf_counter();dest=out/(name+'-'+opt+'-recovered.wasm');p.save(p.w.plain_wat(g['n'],'"run"',t),dest)
            attacks.append({'name':name,'optimization':opt,**a,'read_ms':read_ms,'emit_ms':1000*(time.perf_counter()-start)})
            # Comparable recovered executable receives the same O3 optimization.
            optimized=out/(name+'-'+opt+'-recovered-O3.wasm');p.w.tool('wasm-opt',[dest,'-O3','--enable-bulk-memory','-o',optimized])
            manifest+=[{'name':name,'mode':'recovered-'+opt,'optimization':o,'file':f.name,'bytes':f.stat().st_size,'memory_bytes':0} for o,f in [('raw',dest),('O3',optimized)]]
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));(out/'attacks.json').write_text(json.dumps(attacks,indent=2))
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=60)
    (out/'check.stdout.txt').write_text(r.stdout);(out/'check.stderr.txt').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()},indent=2))

if __name__=='__main__':main(sys.argv[1])
