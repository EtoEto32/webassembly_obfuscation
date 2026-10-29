import argparse,json,platform,random,shutil,subprocess
from pathlib import Path
import prototype as p
HERE=Path(__file__).resolve().parent
def source(n,kind):
    rng=random.Random(4419+n+kind);terms=[];spec=[]
    for i in range(n):
        c=rng.getrandbits(32)|1;r=1+i%31;spec.append([c,r])
        x,y,z=p.g(0),p.g(1),p.g(2)
        rot=lambda e:['i32.rotl',e,p.c(r)]
        if kind==0:e=['i32.mul',rot(['i32.add',x,p.c(c)]),['i32.add',y,p.c(i+1)]]
        elif kind==1:e=['i32.mul',['i32.xor',x,p.c(c)],rot(['i32.add',y,z])]
        else:e=['i32.mul',rot(['i32.xor',x,p.c(c)]),['i32.add',z,y]]
        terms.append(e)
    return p.module([p.sumexpr(terms)]),spec
def main(out,small=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir();snap=[]
    for f in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),HERE/'plan.md',p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        name=str(f.relative_to(p.ROOT)).replace('\\','__').replace('/','__');shutil.copyfile(f,out/'sources'/name);snap.append(dict(path=str(f.relative_to(p.ROOT)),snapshot=name,sha256=p.digest(f)))
    p.save(out/'sources.json',snap);p.save(out/'environment.json',dict(python=platform.python_version(),os=platform.platform(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.w.tool('wat2wasm',['--version']).strip(),binaryen=p.tool('wasm-opt',['--version']).strip()));rows=[];neg=[]
    for n in ([8] if small else [16,32,64]):
        for kind in ([0] if small else range(3)):
            m,spec=source(n,kind);src=out/f'n{n}-k{kind}-source.wasm';p.compile(p.w.emit(m),src);truth=p.recover(src)['terms']
            for mode in ('plain','packed','csa','splitadd','splitcsa'):
                raw=out/f'n{n}-k{kind}-{mode}-raw.wasm';info=p.transform(src,raw,mode)
                for opt in ('raw','O3'):
                    f=raw if opt=='raw' else out/f'n{n}-k{kind}-{mode}-O3.wasm'
                    if opt=='O3':p.tool('wasm-opt',[raw,'--enable-simd','-O3','-o',f])
                    recovered=out/(f.stem+'-recovered.wasm')
                    try:a=p.recover(f,recovered)
                    except Exception as e:p.save(out/'failure.json',dict(file=f.name,exception=type(e).__name__,message=str(e),completed=len(rows)));raise
                    row=dict(info,n=n,kind=kind,spec=spec,opt=opt,source=src.name,file=f.name,recovered=recovered.name,sha256=p.digest(f),recovered_sha256=p.digest(recovered),bytes=f.stat().st_size,attack=a,term_match=a['terms']==truth)
                    rows.append(row)
            bad=out/f'n{n}-k{kind}-broken.wasm';p.transform(src,bad,'splitcsa',broken=True);neg.append(dict(file=bad.name,n=n,kind=kind,spec=spec))
    p.save(out/'manifest.json',rows);p.save(out/'negative-manifest.json',neg)
    subprocess.run(['node',str(HERE/'check.cjs'),str(out)],check=True,timeout=120)
    checks=json.loads((out/'checks.json').read_text());p.save(out/'summary.json',dict(targets=len(rows),recoveries=len(rows),term_matches=sum(r['term_match'] for r in rows),**checks));print((out/'summary.json').read_text())
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');a.add_argument('--small',action='store_true');v=a.parse_args();main(v.output,v.small)
