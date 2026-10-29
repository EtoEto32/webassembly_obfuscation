import argparse,json,platform,random,shutil,struct,subprocess
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
def main(out,small=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);snap=out/'sources';snap.mkdir();ss=[]
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),HERE/'plan.md',p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        name=str(f.relative_to(p.ROOT)).replace('\\','__').replace('/','__');shutil.copyfile(f,snap/name);ss.append(dict(path=str(f.relative_to(p.ROOT)),snapshot=name,sha256=p.digest(f)))
    p.save(out/'sources.json',ss);p.save(out/'environment.json',dict(python=platform.python_version(),os=platform.platform(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.w.tool('wat2wasm',['--version']).strip(),binaryen=p.tool('wasm-opt',['--version']).strip()))
    rows=[];negs=[]
    for n in ([8] if small else [8,32,128]):
        rng=random.Random(2026+n);words=[rng.getrandbits(32) for _ in range(4*n*4)];initial=f'n{n}-initial.json';p.save(out/initial,words);src=out/f'n{n}-source.wasm';p.compile(p.source_text(words,n,4),src);source_probe=out/f'n{n}-source-probe.wasm';p.probe(src,source_probe)
        for depth in ([2] if small else [2,6]):
            for mode in ('plain','full','footprint','patch'):
                raw=out/f'n{n}-d{depth}-{mode}-raw.wasm';info=p.transform(src,raw,n,4,depth,mode)
                for opt in ('raw','O3'):
                    f=raw if opt=='raw' else out/f'n{n}-d{depth}-{mode}-O3.wasm'
                    if opt=='O3':p.tool('wasm-opt',[raw,'--enable-simd','-O3','-o',f])
                    probe=out/(f.stem+'-probe.wasm');p.probe(f,probe)
                    attack={} if mode=='plain' else p.extract_config(f)
                    if mode!='plain':assert attack['coeff']==info['coeff'],(f,attack,info['coeff'])
                    rows.append(dict(info,opt=opt,file=f.name,probe=probe.name,source=src.name,source_probe=source_probe.name,initial=initial,bytes=f.stat().st_size,sha256=p.digest(f),probe_sha256=p.digest(probe),attack=attack))
            bad=out/f'n{n}-d{depth}-broken.wasm';info=p.transform(src,bad,n,4,depth,'broken');probe=out/(bad.stem+'-probe.wasm');p.probe(bad,probe);negs.append(dict(info,file=bad.name,probe=probe.name,initial=initial))
    p.save(out/'manifest.json',rows);p.save(out/'negative-manifest.json',negs)
    subprocess.run(['node',str(HERE/'check.cjs'),str(out)],check=True,timeout=180)
    checks=json.loads((out/'checks.json').read_text());p.save(out/'summary.json',dict(targets=len(rows),negative_witnesses=len(negs),**{k:v for k,v in checks.items() if k!='records'}));print((out/'summary.json').read_text())
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');a.add_argument('--small',action='store_true');v=a.parse_args();main(v.output,v.small)
