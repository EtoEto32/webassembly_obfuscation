import argparse,json,shutil,subprocess
from pathlib import Path
import prototype as p

def fixtures():
    out={}
    for name,predicates in [('axis',[(1,0),(0,1)]),('diagonal',[(1,1),(1,-2)]),('oblique',[(2,1),(-1,2)])]:
        rows=[]
        for a,b in predicates:rows.extend([[1024*a+1,1024*b,512],[1536*a,1536*b+2,768]])
        out[name]=dict(rows=rows,weights=[5,-3,-2,7])
    return out

def run(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);fs=fixtures();targets=[];attacks=[]
    for name,f in fs.items():
        source=out/(name+'.source.wasm');p.q.compile(p.source(f['rows'],f['weights']),source)
        recovered=set()
        for mode in ('plain','perm','mix','bad'):
            raw=out/(name+'.'+mode+'.raw.wasm');meta=p.transform(source,raw,mode)
            opt=out/(name+'.'+mode+'.O3.wasm');p.q.tool('wasm-opt',[raw,'-O3','--enable-simd','-o',opt]);p.q.w.tool('wasm-validate',[opt])
            for kind,file in [('raw',raw),('O3',opt)]:
                targets.append(dict(name=name,mode=mode,opt=kind,file=file.name,bytes=file.stat().st_size,meta=meta,sha256=p.q.digest(file)))
                if mode=='bad':continue
                dst=out/(name+'.'+mode+'.'+kind+'.recovered.wasm');attack=p.recover(file,dst)
                recovered.add(dst.read_bytes());attacks.append(dict(file=file.name,output=dst.name,**attack))
                targets.append(dict(name=name,mode='recovered',origin_mode=mode,opt=kind,file=dst.name,bytes=dst.stat().st_size,sha256=p.q.digest(dst)))
        assert len(recovered)==1,(name,len(recovered))
    p.q.save(out/'manifest.json',dict(fixtures=fs,targets=targets))
    p.q.save(out/'analysis.json',attacks)
    result=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stdout.txt').write_text(result.stdout,encoding='utf-8');(out/'stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stderr)
    sources=out/'sources';sources.mkdir()
    for src in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),p.ROOT/'research/prefix-repair/prototype.py',p.ROOT/'research/copy-centralizer/model.py',p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(src,sources/'__'.join(src.relative_to(p.ROOT).parts))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(targets=len(targets),recovered=len(attacks))))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
