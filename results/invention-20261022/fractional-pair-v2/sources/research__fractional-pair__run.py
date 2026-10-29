import argparse,json,shutil,subprocess
from pathlib import Path
import prototype as p
import model

def run(output):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);targets=[];attacks=[]
    for name in ('pair','chain','euclid'):
        src=out/(name+'.source.wasm');p.q.compile(p.fixture(name),src)
        for mode in ('plain','qsub','zero','fraction','bad'):
            raw=out/(name+'.'+mode+'.raw.wasm');meta=p.transform(src,raw,mode)
            opt=out/(name+'.'+mode+'.O3.wasm');p.q.tool('wasm-opt',[raw,'-O3','-o',opt])
            for kind,file in [('raw',raw),('O3',opt)]:
                p.q.w.tool('wasm-validate',[file]);ast=p.q.read(file)
                targets.append(dict(name=name,mode=mode,opt=kind,file=file.name,meta=meta,bytes=file.stat().st_size,sha256=p.q.digest(file),i64_div=sum(e[0]=='i64.div_u' for e in p.q.walk(ast))))
                if mode not in ('zero','fraction'):continue
                recovered=out/(file.stem+'.recovered.wasm')
                try:attack=p.recover(file,recovered)
                except ValueError as e:
                    attacks.append(dict(file=file.name,status='unsupported',reason=str(e)));continue
                attacks.append(dict(file=file.name,status='recovered',output=recovered.name,**attack))
                targets.append(dict(name=name,mode='recovered',origin_mode=mode,opt=kind,file=recovered.name,bytes=recovered.stat().st_size,sha256=p.q.digest(recovered)))
    p.q.save(out/'manifest.json',dict(targets=targets));p.q.save(out/'analysis.json',attacks)
    model.run(out/'model.json')
    result=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=180)
    (out/'stdout.txt').write_text(result.stdout,encoding='utf-8');(out/'stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stderr)
    snap=out/'sources';snap.mkdir()
    for src in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(src,snap/'__'.join(src.relative_to(p.ROOT).parts))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(targets=len(targets),recovered=sum(a['status']=='recovered' for a in attacks))))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');run(ap.parse_args().output)
