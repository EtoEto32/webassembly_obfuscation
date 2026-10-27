import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import attack
import prototype as p
from shared import h


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);transforms=[];attacks=[]
    for name in ('mix8','select10','chain12'):
        src=out/(name+'-plain.wasm');shutil.copyfile(base/src.name,src);h.w.tool('wasm-opt',[src,'-O3','-o',src.with_name(src.stem+'-O3.wasm')])
        for mode in ('pipeline','feedback'):
            dest=out/(name+'-'+mode+'.wasm');meta=p.transform(src,dest,mode);transforms.append({'name':name,'mode':mode,**meta});opt=dest.with_name(dest.stem+'-O3.wasm');h.w.tool('wasm-opt',[dest,'-O3','--enable-bulk-memory','-o',opt]);h.w.tool('wasm-validate',[opt])
            for inp in (dest,opt):
                result=attack.run(inp,out/(inp.stem+'-recovered.wasm'));attacks.append({'name':name,'mode':mode,'optimization':'O3' if inp==opt else 'raw',**result});print(json.dumps({'name':name,'mode':mode,'file':inp.name,'status':result['status'],'analysis_ms':result['elapsed_ms']}),flush=True)
    (out/'experiment.json').write_text(json.dumps({'transformations':transforms,'attacks':attacks},indent=2))
    check=subprocess.run(['node',str(h.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=180);(out/'check.stdout.log').write_text(check.stdout);(out/'check.stderr.log').write_text(check.stderr)
    if check.returncode:raise RuntimeError(check.stderr)
    (out/'pins.json').write_text(json.dumps({str(f.relative_to(h.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file() and f.name!='pins.json'},indent=2));print(check.stdout)

if __name__=='__main__':main(*sys.argv[1:])
