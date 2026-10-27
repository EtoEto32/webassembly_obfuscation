import json
from pathlib import Path
import random
import subprocess
import sys
import prototype as p


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    rng=random.Random(20261023);cases=[];manifest=[];transforms=[];attacks=[];identities=[]
    for n in (4,16,128):
        for v in range(2):
            name='n%d-v%d'%(n,v);edges=[rng.randrange(n) for _ in range(n)];payload=[rng.getrandbits(32) for _ in range(n)]
            cases.append(dict(name=name,edges=edges,payload=payload));src=out/(name+'-plain-raw.wasm');p.q.compile(p.render(edges,payload),src)
            for mode in ('plain','fixed','moving'):
                raw=out/(name+'-'+mode+'-raw.wasm')
                if mode!='plain':transforms.append(dict(name=name,**p.transform(src,raw,mode,20261023+v)))
                _,_,_,perm=p.recognize(raw,[mode])
                for opt in ('raw','O3'):
                    f=out/(name+'-'+mode+'-'+opt+'.wasm')
                    if opt=='O3':p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',f]);p.q.w.tool('wasm-validate',[f])
                    def record(file,kind,**extra):
                        manifest.append(dict(name=name,mode=kind,opt=opt,file=file.name,bytes=file.stat().st_size,sha256=p.q.digest(file),**extra))
                    record(f,mode)
                    if mode!='plain':
                        dst=f.with_name(f.stem+'-recovered.wasm');attacks.append(dict(name=name,opt=opt,mode=mode,**p.recover(f,dst)));record(dst,'recovered')
                        same=dst.read_bytes()==src.read_bytes();identities.append(dict(name=name,mode=mode,opt=opt,same_source_bytes=same))
                        if not same:raise AssertionError('byte recovery')
                    diag=f.with_name(f.stem+'-diagnostic.wasm');p.q.compile(p.render(edges,payload,mode,perm,True),diag)
                    if opt=='O3':
                        # Separate raw diagnostic input from its O3 derivative.
                        dopt=diag.with_name(diag.stem+'-optimized.wasm');p.q.w.tool('wasm-opt',[diag,'--enable-bulk-memory','-O3','-o',dopt]);diag=dopt
                    record(diag,mode,diagnostic=True)
                if mode=='moving':
                    bad=out/(name+'-bad-order.wasm');p.q.compile(p.render(edges,payload,'bad-order',perm,True),bad)
                    manifest.append(dict(name=name,mode='bad-order',file=bad.name,negative=True))
            print(json.dumps(dict(done=name)),flush=True)
    for name,value in [('cases',cases),('manifest',manifest),('transformations',transforms),('attacks',attacks),('identities',identities)]:p.q.save(out/(name+'.json'),value)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],text=True,capture_output=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout);(out/'checks.stderr.txt').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    checks=json.loads(r.stdout);p.q.save(out/'checks.json',checks)
    print(json.dumps({k:v for k,v in checks.items() if k not in ('rows','negative')}))


if __name__=='__main__':main(sys.argv[1])
