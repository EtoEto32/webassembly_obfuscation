import json
from pathlib import Path
import random
import subprocess
import sys
import prototype as p


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);rng=random.Random(20261023)
    targets=[];cases=[];transformations=[];attacks=[]
    for n in (4,32,256):
        for k in (0,1,257):
            name='n%d-k%d'%(n,k);xs=[rng.getrandbits(32) for _ in range(n)]
            cases.append(dict(name=name,n=n,k=k,initial=xs,erased_bits=p.erased(k)))
            src=out/(name+'-plain-raw.wasm');p.q.compile(p.render(xs,k),src)
            for mode in ('plain','representative','canonical'):
                raw=out/(name+'-'+mode+'-raw.wasm')
                if mode!='plain':transformations.append(dict(name=name,mode=mode,**p.transform(src,raw,mode)))
                for opt in ('raw','O3'):
                    f=out/(name+'-'+mode+'-'+opt+'.wasm')
                    if opt=='O3':p.q.w.tool('wasm-opt',[raw,'-O3','-o',f]);p.q.w.tool('wasm-validate',[f])
                    targets.append(dict(name=name,mode=mode,optimization=opt,file=f.name,bytes=f.stat().st_size,sha256=p.q.digest(f)))
                    if mode!='plain':
                        dest=f.with_name(f.stem+'-recovered.wasm');attacks.append(dict(name=name,mode=mode,optimization=opt,**p.recover(f,dest)))
                        targets.append(dict(name=name,mode=mode+'-recovered',optimization=opt,file=dest.name,bytes=dest.stat().st_size,sha256=p.q.digest(dest)))
            # A genuine information erasure collision in the allowed family.
            if p.erased(k):
                step=1<<(32-p.erased(k));other=[(v+step)&p.MASK for v in xs]
                alternate=out/(name+'-alternate-source.wasm');p.q.compile(p.render(other,k),alternate)
                for mode in ('canonical','representative'):
                    dst=out/(name+'-alternate-'+mode+'.wasm');p.transform(alternate,dst,mode)
                    if dst.read_bytes()!=(out/(name+'-'+mode+'-raw.wasm')).read_bytes():raise AssertionError('quotient collision failed')
            print(json.dumps(dict(done=name)),flush=True)
    for file,obj in [('cases.json',cases),('manifest.json',targets),('transformations.json',transformations),('attacks.json',attacks)]:p.q.save(out/file,obj)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr)
    p.q.save(out/'checks.json',json.loads(r.stdout))
    summary=json.loads(r.stdout);print(json.dumps({k:summary[k] for k in ('binaries','calls','traps','mismatches')}),flush=True)


if __name__=='__main__':main(sys.argv[1])
