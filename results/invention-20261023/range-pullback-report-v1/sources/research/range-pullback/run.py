import json
from pathlib import Path
import random
import subprocess
import sys
import prototype as p


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rng=random.Random(20261023)
    cases=[];targets=[];transforms=[];attacks=[];identities=[]
    for n in (2,4,8):
        for variant in range(2):
            name='c%d-v%d'%(n,variant);data=bytes(rng.randrange(256) for _ in range(4096));indices=list(range(3*n));rng.shuffle(indices);plan=[indices[3*i:3*i+3] for i in range(n)]
            cases.append(dict(name=name,initial=list(data),plan=plan));src=out/(name+'-plain-raw.wasm');p.q.compile(p.render(data,plan),src)
            raw=out/(name+'-pullback-raw.wasm');transforms.append(dict(name=name,**p.transform(src,raw)))
            for mode in ('plain','pullback'):
                raw=out/(name+'-'+mode+'-raw.wasm')
                for opt in ('raw','O3'):
                    f=out/(name+'-'+mode+'-'+opt+'.wasm')
                    if opt=='O3':p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',f]);p.q.w.tool('wasm-validate',[f])
                    def record(file,kind):targets.append(dict(name=name,mode=kind,opt=opt,file=file.name,bytes=file.stat().st_size,sha256=p.q.digest(file)))
                    record(f,mode)
                    if mode=='pullback':
                        dst=f.with_name(f.stem+'-recovered.wasm');attacks.append(dict(name=name,opt=opt,**p.recover(f,dst)));record(dst,'recovered')
                        same=dst.read_bytes()==src.read_bytes();identities.append(dict(name=name,opt=opt,same_source_bytes=same))
                        if not same:raise AssertionError('not exact source recovery')
            for label,text in [('missing-bounds',p.render(data,plan,'pullback',False)),('wrong-order',p.render(data,list(reversed(plan)),'pullback'))]:
                f=out/(name+'-'+label+'.wasm');p.q.compile(text,f);targets.append(dict(name=name,mode=label,file=f.name,negative=True))
            print(json.dumps(dict(done=name)),flush=True)
    for file,obj in [('cases',cases),('manifest',targets),('transformations',transforms),('attacks',attacks),('identities',identities)]:p.q.save(out/(file+'.json'),obj)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout);(out/'checks.stderr.txt').write_text(r.stderr)
    if r.returncode:raise RuntimeError(r.stderr)
    result=json.loads(r.stdout);p.q.save(out/'checks.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('rows','negative')}))


if __name__=='__main__':main(sys.argv[1])
