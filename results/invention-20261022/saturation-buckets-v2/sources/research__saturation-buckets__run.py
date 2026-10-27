import argparse, json, random, shutil, subprocess
from pathlib import Path
import prototype as p

def fixtures():
    rng=random.Random(221022)
    result={}
    for name,bits,n in [('small12',[4]*8,12),('mixed48',[2,3,4,5,6,7,8,4],48),('byte128',[8]*8,128)]:
        ops=[dict(sign='+' if i%4 in (0,3) else '-',mask=[rng.randint(0,min((1<<b)-1,7)) for b in bits]) for i in range(n)]
        result[name]=dict(bits=bits,ops=ops)
    return result

def run(output):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
    fs=fixtures();targets=[];attacks=[]
    for name,f in fs.items():
        src=out/(name+'.source.wasm');p.q.compile(p.source(f['bits'],f['ops']),src)
        recovered=set()
        for mode in ('plain','native8','canonical','zero','bucket','bad'):
            raw=out/(name+'.'+mode+'.raw.wasm');meta=p.transform(src,raw,mode)
            opt=out/(name+'.'+mode+'.O3.wasm');p.q.tool('wasm-opt',[raw,'-O3','--enable-simd','-o',opt]);p.q.w.tool('wasm-validate',[opt])
            for kind,file in [('raw',raw),('O3',opt)]:
                targets.append(dict(name=name,mode=mode,opt=kind,file=file.name,meta=meta,sha256=p.q.digest(file),bytes=file.stat().st_size))
                if mode=='bad':continue
                log=out/(file.stem+'.learn.json')
                result=subprocess.run(['node',str(Path(__file__).with_name('learn.cjs')),str(file),str(log)],capture_output=True,text=True,timeout=60)
                if result.returncode:raise RuntimeError(result.stderr)
                learned=json.loads(log.read_text());dst=out/(file.stem+'.recovered.wasm');p.recovered(learned['tables'],dst)
                recovered.add(dst.read_bytes());attacks.append(dict(file=file.name,output=dst.name,log=log.name,queries=learned['queries'],elapsed_ms=learned['elapsedMs'],sha256=p.q.digest(dst)))
                targets.append(dict(name=name,mode='recovered',origin_mode=mode,opt=kind,file=dst.name,sha256=p.q.digest(dst),bytes=dst.stat().st_size))
        assert len(recovered)==1,(name,len(recovered))
    p.q.save(out/'manifest.json',dict(fixtures=fs,targets=targets));p.q.save(out/'analysis.json',attacks)
    result=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=180)
    (out/'stdout.txt').write_text(result.stdout,encoding='utf-8');(out/'stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stderr)
    sources=out/'sources';sources.mkdir()
    for src in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(src,sources/'__'.join(src.relative_to(p.ROOT).parts))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(targets=len(targets),recovered=len(attacks))))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
