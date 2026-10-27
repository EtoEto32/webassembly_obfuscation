"""Supplemental real-Wasm coverage of a nonzero fourth-degree component."""
import json
from pathlib import Path
import random
import subprocess
import sys
import prototype as p


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);cases=[];targets=[];attacks=[];degrees=[];rng=random.Random(20261023)
    base=[{(1,2):1},{(-1,):1,(1,1):1,(0,2):1},{(-2,):1}]
    for weighted in (False,True):
        name='branching'+('-weighted' if weighted else '')
        ps=[{word:((rng.getrandbits(32)|1) if weighted else value) for word,value in poly.items()} for poly in base]
        g=p.binarize(ps,2);cases.append(dict(name=name,grammar=g));src=out/(name+'-plain-raw.wasm');p.q.compile(p.render(g),src)
        for alpha in (0,1,257,65536):
            raw=out/(name+('-nonlinear-%d-raw.wasm'%alpha if alpha else '-plain-raw.wasm'))
            if alpha:
                p.transform(src,raw,1,0,2,alpha)
                h=p.shear(ps,1,0,2,alpha);degree=max(len(w) for poly in h for w in poly)
                if degree!=(3 if alpha==65536 else 4):raise AssertionError('missing quartic control')
                degrees.append(dict(name=name,alpha=alpha,degree=degree))
            for opt in ('raw','O3'):
                f=raw if opt=='raw' else raw.with_name(raw.name.replace('-raw','-O3'))
                if opt=='O3':p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',f]);p.q.w.tool('wasm-validate',[f])
                targets.append(dict(name=name,mode='nonlinear' if alpha else 'plain',optimization=opt,file=f.name,bytes=f.stat().st_size,sha256=p.q.digest(f)))
                if alpha:
                    dst=f.with_name(f.stem+'-recovered.wasm');r=p.recover(f,dst,weighted=True)
                    attacks.append(dict(name=name,source_alpha=alpha,optimization=opt,**r))
                    if r['status']=='recovered':targets.append(dict(name=name,mode='recovered',optimization=opt,file=dst.name,bytes=dst.stat().st_size,sha256=p.q.digest(dst)))
    for name,x in [('cases',cases),('manifest',targets),('attacks',attacks),('degrees',degrees)]:p.q.save(out/(name+'.json'),x)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout);(out/'checks.stderr.txt').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    result=json.loads(r.stdout);p.q.save(out/'checks.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':main(sys.argv[1])
