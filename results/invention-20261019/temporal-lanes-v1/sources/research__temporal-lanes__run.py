import argparse,json,platform,random,shutil,subprocess
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
def main(out,small=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();ss=[]
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),HERE/'plan.md',p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        name=str(f.relative_to(p.ROOT)).replace('\\','__').replace('/','__');shutil.copyfile(f,out/'sources'/name);ss.append(dict(path=str(f.relative_to(p.ROOT)),snapshot=name,sha256=p.digest(f)))
    p.save(out/'sources.json',ss);p.save(out/'environment.json',dict(python=platform.python_version(),os=platform.platform(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.w.tool('wat2wasm',['--version']).strip(),binaryen=p.tool('wasm-opt',['--version']).strip()))
    rows=[];negative=[]
    for n in ([4] if small else [4,8,16]):
        for kind in ([0] if small else range(3)):
            rng=random.Random(20261019+n+kind);coeff=[rng.randrange(0x10001,0x7fffffff)|1 for _ in range(n)];spec=dict(n=n,kind=kind,r=7+kind*5,coeff=coeff)
            src=out/f'n{n}-k{kind}-source.wasm';p.compile(p.w.emit(p.source(coeff,kind,spec['r'])),src);sourceprobe=out/(src.stem+'-probe.wasm');p.probe(src,sourceprobe)
            for mode in ('plain','scalar','vector','mixed'):
                raw=out/f'n{n}-k{kind}-{mode}-raw.wasm';info=p.transform(src,raw,mode)
                for opt in ('raw','O3'):
                    f=raw if opt=='raw' else out/f'n{n}-k{kind}-{mode}-O3.wasm'
                    if opt=='O3':p.tool('wasm-opt',[raw,'--enable-simd','-O3','-o',f])
                    probe=out/(f.stem+'-probe.wasm');p.probe(f,probe)
                    row=dict(info,opt=opt,file=f.name,probe=probe.name,source=src.name,source_probe=sourceprobe.name,sha256=p.digest(f),probe_sha256=p.digest(probe),bytes=f.stat().st_size)
                    if mode in ('vector','mixed'):
                        try:attack=p.extract(f)
                        except Exception as e:
                            p.save(out/'failure.json',dict(file=f.name,exception=type(e).__name__,message=str(e),completed=len(rows)));raise
                        assert all(attack[k]==spec[k] for k in ('n','kind','r','coeff')),(row,attack,spec)
                        recovered=out/(f.stem+'-recovered.wasm');p.compile(p.w.emit(p.source(attack['coeff'],attack['kind'],attack['r'])),recovered)
                        rp=out/(f.stem+'-recovered-probe.wasm');p.probe(recovered,rp);row.update(attack=attack,recovered=recovered.name,recovered_probe=rp.name,recovered_sha256=p.digest(recovered),recovered_probe_sha256=p.digest(rp))
                    rows.append(row)
            bad=out/f'n{n}-k{kind}-broken.wasm';p.compile(p.w.emit(p.build(spec,'mixed',broken=True)),bad);bp=out/(bad.stem+'-probe.wasm');p.probe(bad,bp);negative.append(dict(spec,file=bad.name,probe=bp.name))
    p.save(out/'manifest.json',rows);p.save(out/'negative-manifest.json',negative)
    subprocess.run(['node',str(HERE/'check.cjs'),str(out)],check=True,timeout=180)
    checks=json.loads((out/'checks.json').read_text());summary=dict(targets=len(rows),recoveries=sum('attack' in r for r in rows),**{k:v for k,v in checks.items() if k!='records'})
    p.save(out/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');a.add_argument('--small',action='store_true');v=a.parse_args();main(v.output,v.small)
