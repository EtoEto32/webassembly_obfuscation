import json
from pathlib import Path
import shutil
import subprocess
import sys
import coupled
import attack
from shared import h,a


def main(base,out):
    base=Path(base).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rows=[];old=[]
    for name in ('mix8','select10','chain12'):
        src=out/(name+'-plain.wasm');shutil.copyfile(base/src.name,src);h.w.tool('wasm-opt',[src,'-O3','-o',src.with_name(src.stem+'-O3.wasm')])
        for mode in ('pipeline','feedback','coupled'):
            dest=out/(name+'-'+mode+'.wasm');meta=coupled.transform(src,dest,mode);opt=dest.with_name(dest.stem+'-O3.wasm');h.w.tool('wasm-opt',[dest,'-O3','--enable-bulk-memory','-o',opt]);h.w.tool('wasm-validate',[opt]);r,_=a.read(dest)
            groups,deps=attack.components([{tuple(m) for m in poly} for poly in r['maps']],r['n']);rows.append({'name':name,'mode':mode,'file':dest.name,'scc_sizes':[len(g) for g in groups],**meta})
            if mode=='coupled':
                for source in (dest,opt):
                    try:result=attack.run(source,out/(source.stem+'-old-recovered.wasm'));old.append({'file':source.name,**result})
                    except ValueError as e:old.append({'file':source.name,'status':'unsupported','reason':str(e)})
            print(json.dumps({'name':name,'mode':mode,'scc_sizes':rows[-1]['scc_sizes'],'terms':meta['terms']}),flush=True)
    (out/'manifest.json').write_text(json.dumps(rows,indent=2));(out/'old-attacks.json').write_text(json.dumps(old,indent=2))
    check=subprocess.run(['node',str(h.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=180);(out/'check.stdout.log').write_text(check.stdout);(out/'check.stderr.log').write_text(check.stderr)
    if check.returncode:raise RuntimeError(check.stderr)
    print(check.stdout)

if __name__=='__main__':main(*sys.argv[1:])
