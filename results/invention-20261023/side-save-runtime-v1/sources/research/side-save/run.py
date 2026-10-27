import json
from pathlib import Path
import random
import subprocess
import sys
import time
import traceback
import prototype as p

FIXTURES={'swap16':(16,[(15,0,1),(0,1,1),(1,15,1)]),
          'rotate32':(32,[(28,0,4),(0,4,24),(24,28,4)]),
          'ladder64':(64,[(63,0,1),(0,8,1),(8,16,1),(16,24,1),(24,32,1),(32,63,1)])}


def safe(v):
    if isinstance(v,int) and abs(v)>=2**53:return str(v)
    if isinstance(v,(list,tuple)):return [safe(x) for x in v]
    if isinstance(v,dict):return {k:safe(x) for k,x in v.items()}
    return v


def main(dest):
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False);targets=[];fixtures={};attacks=[];attacker=p.recovery()
    for name,(n,ops) in FIXTURES.items():
        rng=random.Random(20261021+n);data=bytes(rng.randrange(256) for _ in range(n));fixtures[name]=dict(n=n,ops=ops,data=list(data))
        src=out/(name+'.source.wasm');p.q.compile(p.base.wat(data,ops),src)
        for seed,mode in [(0,'plain')]+[(s,mode) for s in (211070,211071) for mode in ('basis','side','bad')]:
            raw=out/f'{name}.{seed}.{mode}.raw.wasm'
            if mode=='plain':p.q.compile(p.base.wat(data,ops),raw);meta=dict(n=n,ops=ops,matrix=p.m.ident(n),transform_ms=0)
            else:meta=p.transform(src,raw,mode,seed)
            opt=out/f'{name}.{seed}.{mode}.O3.wasm';p.q.w.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',opt])
            for kind,f in [('raw',raw),('O3',opt)]:
                probe=out/(f.stem+'.probe.wasm');p.base.probe(f,probe)
                targets.append(dict(name=name,seed=seed,mode=mode,opt=kind,file=f.name,probe=probe.name,bytes=f.stat().st_size,meta=meta))
                if mode not in ('basis','side'):continue
                recovered=out/(f.stem+'.recovered.wasm');start=time.perf_counter()
                try:
                    result=attacker.recover(f,recovered);same=recovered.read_bytes()==src.read_bytes()
                    if not same:raise AssertionError('recovered bytes differ')
                    status=dict(status='success',byte_identical=same,**result)
                except ValueError as ex:status=dict(status='unsupported',reason=str(ex))
                except Exception as ex:status=dict(status='crash',reason=repr(ex))
                attacks.append(dict(file=f.name,mode=mode,ms=(time.perf_counter()-start)*1000,**status))
                if status['status']=='success' and mode=='side':
                    probe=out/(recovered.stem+'.probe.wasm');p.base.probe(recovered,probe)
                    targets.append(dict(name=name,seed=seed,mode='recovered',opt=kind,file=recovered.name,probe=probe.name,bytes=recovered.stat().st_size,meta=dict(n=n,ops=ops,matrix=p.m.ident(n))))
    p.q.save(out/'manifest.json',safe(dict(targets=targets,fixtures=fixtures)));p.q.save(out/'attacks.json',attacks)
    check=subprocess.run(['node',str(p.ROOT/'research/prefix-repair/check.cjs'),str(out)],capture_output=True,text=True,timeout=180)
    (out/'stdout.txt').write_text(check.stdout,encoding='utf-8');(out/'stderr.txt').write_text(check.stderr,encoding='utf-8')
    if check.returncode:raise RuntimeError(check.stderr)
    print(check.stdout.strip());print(json.dumps({s:sum(x['status']==s for x in attacks) for s in ('success','unsupported','crash','timeout')}))


if __name__=='__main__':
    try:main(sys.argv[1])
    except Exception:
        out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True);(out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
