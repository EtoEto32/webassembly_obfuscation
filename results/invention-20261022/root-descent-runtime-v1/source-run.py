import argparse,json,shutil,subprocess
from pathlib import Path
import prototype as p
import attack

FIXTURES={
 'arith':'(local.set 3 (i32.add (local.get 0) (local.get 1))) (local.set 4 (i32.xor (local.get 3) (local.get 2))) (i32.mul (local.get 4) (local.get 3))',
 'blend':'(local.set 3 (i32.and (local.get 0) (local.get 1))) (local.set 4 (i32.add (local.get 3) (local.get 2))) (i32.xor (local.get 4) (local.get 1))',
 'product':'(local.set 3 (i32.mul (local.get 0) (local.get 1))) (local.set 4 (i32.add (local.get 3) (local.get 1))) (i32.or (local.get 4) (local.get 2))'}

def pin(out):
    for f in Path(__file__).parent.iterdir():
        if f.suffix in ('.py','.cjs'):shutil.copy2(f,out/('source-'+f.name))
    p.save(out/'commands.json',p.w.LOG)
    p.save(out/'pins.json',{str(f.relative_to(out)):p.digest(f) for f in out.rglob('*') if f.is_file()})

def run(output):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);rows=[];analyses=[];transforms=[];prior=[]
    for name,body in FIXTURES.items():
        plain=out/f'{name}.plain.raw.wasm';p.compile_wat(f'(module (func (export "run") (param i32 i32 i32) (result i32) (local i32 i32) {body}))',plain)
        for mode in ('plain','constant','congruent','rotated','bad'):
            raw=out/f'{name}.{mode}.raw.wasm'
            if mode!='plain':transforms.append(dict(name=name,**p.transform(plain,raw,mode)))
            opt=out/f'{name}.{mode}.O3.wasm';p.tool('wasm-opt',[raw,'-O3','-o',opt]);p.tool('wasm-validate',[opt])
            for kind,src in (('raw',raw),('O3',opt)):
                rows.append(dict(name=name,mode=mode,opt=kind,file=src.name,negative=mode=='bad'))
                if mode!='plain':
                    try:
                        wat,stats=attack.extract(src)
                        if mode=='bad':raise AssertionError('negative accepted')
                        dst=out/f'{name}.{mode}.{kind}.recovered.wasm';p.compile_wat(wat,dst)
                        rows.append(dict(name=name,mode=mode+'-recovered',opt=kind,file=dst.name,negative=False))
                    except (ValueError,RuntimeError) as e:stats=dict(status='rejected' if mode=='bad' else 'unsupported',error=str(e))
                    analyses.append(dict(name=name,mode=mode,opt=kind,**stats));p.save(out/'analysis.json',analyses)
                if mode in ('constant','congruent','rotated'):
                    try:
                        result=p.bitrecover.recover(src)
                        prior.append(dict(name=name,mode=mode,opt=kind,status='recovered',details=result))
                    except (ValueError,RuntimeError,RecursionError) as e:
                        prior.append(dict(name=name,mode=mode,opt=kind,status='cycle' if 'cycle' in str(e) else 'unsupported',error=str(e)))
    p.save(out/'manifest.json',rows);p.save(out/'transforms.json',transforms);p.save(out/'dependency-attack.json',prior)
    r=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=180)
    (out/'check.stdout.txt').write_text(r.stdout,encoding='utf-8');(out/'check.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr or r.stdout)
    pin(out);print(r.stdout)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
