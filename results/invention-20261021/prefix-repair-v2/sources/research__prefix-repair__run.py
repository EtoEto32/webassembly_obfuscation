import argparse
import json
import random
import shutil
import subprocess
from pathlib import Path
import prototype as p

FIXTURES={
 'swap16':(16,[(15,0,1),(0,1,1),(1,15,1)]),
 'rotate32':(32,[(28,0,4),(0,4,24),(24,28,4)]),
 'ladder64':(64,[(63,0,1),(0,8,1),(8,16,1),(16,24,1),(24,32,1),(32,63,1)])}

def safe(value):
    if isinstance(value,int) and abs(value)>=2**53:return str(value)
    if isinstance(value,list):return [safe(x) for x in value]
    if isinstance(value,dict):return {k:safe(v) for k,v in value.items()}
    return value

def run(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    targets=[]
    for name,(n,ops) in FIXTURES.items():
        rng=random.Random(n+20261021);data=bytes(rng.randrange(256) for _ in range(n));src=out/(name+'.source.wasm');p.q.compile(p.wat(data,ops),src)
        for seed in (211070,211071):
            for mode in ('plain','eager','full','basis','bad'):
                raw=out/(name+'.'+str(seed)+'.'+mode+'.raw.wasm')
                if mode=='plain':
                    p.q.compile(p.wat(data,ops),raw);meta=dict(n=n,ops=ops,mode=mode,seed=seed,matrix=p.m.ident(n),inverse=p.m.ident(n),transform_ms=0)
                else:meta=p.transform(src,raw,mode,seed)
                opt=out/(raw.stem.replace('.raw','.O3')+'.wasm');p.q.tool('wasm-opt',[raw,'-O3','--enable-bulk-memory','-o',opt]);p.q.w.tool('wasm-validate',[opt])
                for kind,file in [('raw',raw),('O3',opt)]:
                    probe=out/(file.stem+'.probe.wasm');p.probe(file,probe)
                    targets.append(dict(name=name,seed=seed,mode=mode,opt=kind,file=file.name,probe=probe.name,bytes=file.stat().st_size,sha256=p.q.digest(file),meta=meta))
    manifest=dict(targets=targets,fixtures=FIXTURES,positive_modes=['plain','eager','full','basis'],negative_mode='bad')
    p.q.save(out/'manifest.json',safe(manifest))
    r=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stdout.txt').write_text(r.stdout,encoding='utf-8');(out/'stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr)
    snapshot=out/'sources';snapshot.mkdir()
    for f in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),p.ROOT/'research/copy-centralizer/model.py',p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(f,snapshot/'__'.join(f.relative_to(p.ROOT).parts))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps({'targets':len(targets),'output':str(out)}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
