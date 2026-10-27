import json
from pathlib import Path
import random
import subprocess
import sys
import prototype as p


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    targets=[];cases=[];transforms=[];attacks=[];rng=random.Random(20261023)
    for weighted in (False,True):
        for g in p.grammars():
            name=g['name']+('-weighted' if weighted else '')
            ps=g['polys']
            if weighted:ps=[{w:(rng.getrandbits(32)|1) for w in poly} for poly in ps]
            grammar=p.binarize(ps,g['alphabet']);cases.append(dict(name=name,grammar=grammar,weighted=weighted))
            src=out/(name+'-plain-raw.wasm');p.q.compile(p.render(grammar),src)
            variants=[('plain',None)]
            for alpha in (1,257,65536):
                for mode in (('nonlinear',) if weighted else ('linear','nonlinear')):
                    key=mode+'-'+str(alpha);dst=out/(name+'-'+key+'-raw.wasm')
                    transforms.append(dict(name=name,mode=mode,alpha=alpha,**p.transform(src,dst,g['a'],g['b'],g['c'],alpha,mode=='linear')))
                    variants.append((key,mode))
            for key,mode in variants:
                for opt in ('raw','O3'):
                    raw=out/(name+'-'+key+'-raw.wasm');f=out/(name+'-'+key+'-'+opt+'.wasm')
                    if opt=='O3':p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',f]);p.q.w.tool('wasm-validate',[f])
                    def record(file,kind):
                        targets.append(dict(name=name,mode=kind,optimization=opt,file=file.name,bytes=file.stat().st_size,sha256=p.q.digest(file)))
                    record(f,key)
                    if mode:
                        dst=out/(f.stem+'-recovered.wasm');r=p.recover(f,dst,mode=='linear',weighted)
                        attacks.append(dict(name=name,mode=key,optimization=opt,weighted=weighted,**r))
                        if r['status']=='recovered':record(dst,key+'-recovered')
            print(json.dumps(dict(done=name)),flush=True)
    for name,x in [('cases',cases),('manifest',targets),('transformations',transforms),('attacks',attacks)]:p.q.save(out/(name+'.json'),x)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout);(out/'checks.stderr.txt').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    result=json.loads(r.stdout);p.q.save(out/'checks.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':main(sys.argv[1])
