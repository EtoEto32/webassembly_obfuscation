import argparse
import json
import shutil
import subprocess
import traceback
from pathlib import Path
import prototype as p
import recover as r


def pattern(text, absorbing):
    n=len(text);delta=[]
    for state in range(n+1):
        row=[]
        for a in '01':
            if absorbing and state==n:row.append(n);continue
            word=text[:state]+a
            row.append(max(k for k in range(n+1) if word.endswith(text[:k])))
        delta.append(row)
    return dict(delta=delta,accept=1<<n)


FIXTURES={'suffix001':pattern('001',False),'contains01101':pattern('01101',True),
          'mod7':dict(delta=[[(2*i+a)%7 for a in (0,1)] for i in range(7)],accept=1)}


def run(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    sources=out/'sources';sources.mkdir()
    for file in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),Path(__file__).parent/'plan.md',
                 p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(file,sources/'__'.join(file.relative_to(p.ROOT).parts))
    targets=[];analysis=[]
    for name,f in FIXTURES.items():
        source=out/(name+'.source.wasm');p.q.compile(p.source(f['delta'],f['accept']),source)
        for mode,seed in [('plain',0),('reverse',0),('mixed',221011),('mixed',221012),('bad',221011)]:
            raw=out/f'{name}.{mode}.{seed}.raw.wasm'
            if mode=='plain':p.q.compile(p.source(f['delta'],f['accept']),raw);info={}
            elif mode=='bad':
                wat,info=p.transformed(f['delta'],f['accept'],'mixed',seed)
                initial=p.encode(f['accept'],p.gates(len(f['delta']),seed))
                wat=wat.replace(p.consumer(initial,True),p.consumer(initial,False))
                p.q.compile(wat,raw)
            else:info=p.transform(source,raw,mode,seed)
            opt=out/(raw.stem.replace('.raw','.O3')+'.wasm');p.q.tool('wasm-opt',[raw,'-O3','-o',opt]);p.q.w.tool('wasm-validate',[opt])
            for kind,file in [('raw',raw),('O3',opt)]:
                targets.append(dict(name=name,mode=mode,seed=seed,opt=kind,file=file.name,bytes=file.stat().st_size,sha256=p.q.digest(file),info=info))
                if mode in ('reverse','mixed'):
                    dst=out/(file.stem+'.recovered.wasm');report=r.recover(file,dst)
                    report.update(file=file.name,name=name,mode=mode,opt=kind,seed=seed,source_byte_equal=source.read_bytes()==dst.read_bytes())
                    # All chosen fixtures have BFS numbering and reachable states.
                    assert report['source_byte_equal'],name
                    analysis.append(report)
                    targets.append(dict(name=name,mode='recovered',origin=mode,seed=seed,opt=kind,file=dst.name,bytes=dst.stat().st_size,sha256=p.q.digest(dst),info={}))
    p.q.save(out/'manifest.json',dict(fixtures=FIXTURES,targets=targets))
    p.q.save(out/'analysis.json',analysis)
    result=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=180)
    (out/'stdout.txt').write_text(result.stdout,encoding='utf-8');(out/'stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stderr)
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(targets=len(targets),recoveries=len(analysis),checks=result.stdout)))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args()
    try:run(a.output)
    except Exception:
        d=Path(a.output)
        if d.is_dir() and not(d/'failure.txt').exists():(d/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
