import argparse,json,shutil,subprocess,traceback
from pathlib import Path
import prototype as p
import recover as r

FIXTURES={
    'cubic':[17,5,9,3],
    'septic':[0x1234567,0xfedcba99,3,0x10001,7,0x2468ac,0x80000003,19],
    'degree11':[123456789,0x89abcdef,0x10203,37,0x80000003,0x55555555,17,0xdeadbeef,0x400001,0x70f12345,2,11],
}


def run(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    srcdir=out/'sources';srcdir.mkdir()
    for f in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),Path(__file__).parent/'plan.md',p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']:
        shutil.copy2(f,srcdir/'__'.join(f.relative_to(p.ROOT).parts))
    targets=[];analysis=[];rejections=[]
    for name,a in FIXTURES.items():
        source=out/(name+'.source.wasm');p.q.compile(p.source(a),source)
        for mode in ('plain','naive','delta','bad'):
            raw=out/f'{name}.{mode}.raw.wasm'
            if mode=='plain':p.q.compile(p.source(a),raw);info={}
            else:info=p.transform(source,raw,mode)
            opt=out/f'{name}.{mode}.O3.wasm';p.q.tool('wasm-opt',[raw,'-O3','-o',opt]);p.q.w.tool('wasm-validate',[opt])
            for kind,file in [('raw',raw),('O3',opt)]:
                targets.append(dict(name=name,mode=mode,opt=kind,file=file.name,bytes=file.stat().st_size,sha256=p.q.digest(file),info=info))
                if mode in ('naive','delta'):
                    dst=out/(file.stem+'.recovered.wasm');report=r.recover(file,dst)
                    report.update(name=name,mode=mode,opt=kind,file=file.name,source_coefficients_equal=report['coefficients']==p.trim(a),source_byte_equal=dst.read_bytes()==source.read_bytes())
                    analysis.append(report)
                    targets.append(dict(name=name,mode='recovered',origin=mode,opt=kind,file=dst.name,bytes=dst.stat().st_size,sha256=p.q.digest(dst),info={}))
                elif mode=='bad':
                    try:r.recover(file,out/(file.stem+'.must-not-exist.wasm'))
                    except ValueError as error:rejections.append(dict(file=file.name,error=str(error)))
                    else:raise AssertionError('invalid finite difference accepted')
    p.q.save(out/'manifest.json',dict(fixtures=FIXTURES,targets=targets))
    p.q.save(out/'analysis.json',analysis);p.q.save(out/'rejections.json',rejections)
    check=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=120)
    (out/'stderr.txt').write_text(check.stderr,encoding='utf-8');(out/'stdout.txt').write_text(check.stdout,encoding='utf-8')
    if check.returncode:raise RuntimeError(check.stderr)
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(targets=len(targets),recoveries=len(analysis),rejections=len(rejections),checks=check.stdout)))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args()
    try:run(a.output)
    except Exception:
        if Path(a.output).is_dir():(Path(a.output)/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
