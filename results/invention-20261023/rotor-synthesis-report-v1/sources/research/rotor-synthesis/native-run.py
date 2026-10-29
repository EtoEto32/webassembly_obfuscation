import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import prototype as p
import native

def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[];manifest=[]
    # Copy controls unchanged for a contemporaneous performance comparison.
    for src in base.glob('*.wasm'):
        if src.name.endswith('-O3.wasm'):shutil.copyfile(src,out/src.name)
    for name in ('and3','majority3','mux3'):
        original=base/(name+'-plain.wasm');np,_,formula=p.w.source(original);r=p.read(base/(name+'-rotor.wasm'))
        for mode in ('native','tight'):
            g=copy.deepcopy(r)
            if mode=='tight':g['bound']=max(len(p.simulate(r,x)[1]) for x in range(1<<r['n']))
            src=out/(name+'-'+mode+'.wasm');p.save(native.render(g),src);opt=out/(name+'-'+mode+'-O3.wasm');p.w.tool('wasm-opt',[src,'-O3','--enable-bulk-memory','-o',opt])
            for optimization,path in [('raw',src),('O3',opt)]:
                n,f,a=native.recover(path);assert all(p.evaluate(f,x)==p.evaluate(formula,x) for x in range(1<<n));dest=out/(path.stem+'-recovered.wasm');p.save(p.w.plain_wat(n,'"run"',f),dest)
                rows.append({'name':name,'mode':mode,'optimization':optimization,'bound':g['bound'],**a})
                manifest.extend({'name':name,'mode':m,'optimization':optimization,'file':q.name,'bytes':q.stat().st_size,'memory_bytes':0} for m,q in [(mode,path),('recovered-'+mode,dest)])
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));(out/'attacks.json').write_text(json.dumps(rows,indent=2))
    result=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=60);(out/'check.stdout.txt').write_text(result.stdout);(out/'check.stderr.txt').write_text(result.stderr)
    if result.returncode:raise RuntimeError(result.stderr)
    print(result.stdout)

if __name__=='__main__':main(*sys.argv[1:])
