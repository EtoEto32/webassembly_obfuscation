import argparse
import json
import shutil
import struct
import subprocess
from pathlib import Path
import prototype as p
import recover

# WAT and the JS BigInt oracle are separately written, not generated from each other.
FIXTURES={
 'bilinear':'(i32.sub (i32.mul (i32.add (local.get 0) (local.get 1)) (i32.add (local.get 2) (i32.const 7))) (i32.mul (local.get 0) (local.get 2)))',
 'horner':'(i32.add (i32.mul (i32.add (i32.mul (i32.add (i32.mul (local.get 0) (i32.const 3)) (local.get 1)) (local.get 0)) (local.get 2)) (local.get 0)) (i32.const 17))',
 'product':'(i32.mul (i32.mul (i32.add (i32.add (local.get 0) (local.get 1)) (i32.const 3)) (i32.add (i32.add (local.get 1) (local.get 2)) (i32.const 5))) (i32.add (i32.add (local.get 2) (local.get 0)) (i32.const 7)))'
}


def pin(out):
    for f in Path(__file__).parent.iterdir():
        if f.suffix in ('.py','.cjs','.wat'):
            shutil.copy2(f,out/('source-'+f.name))
    p.save(out/'commands.json',p.LOG)
    p.save(out/'pins.json',{str(f.relative_to(out)):p.digest(f) for f in out.rglob('*') if f.is_file()})


def run(output):
    out=Path(output).resolve(); out.mkdir(parents=True,exist_ok=False)
    accepted=recover.templates(out/'templates'); rows=[]; transforms=[]; analyses=[]
    for name,expr in FIXTURES.items():
        plain=out/f'{name}.plain.raw.wasm'
        p.compile_wat(f'(module (func (export "run") (param i32 i32 i32) (result i32) {expr}))',plain)
        for mode in ('plain','unmixed','constant','polynomial'):
            raw=out/f'{name}.{mode}.raw.wasm'
            if mode!='plain': transforms.append(dict(name=name,**p.transform(plain,raw,mode)))
            opt=out/f'{name}.{mode}.O3.wasm'; p.tool('wasm-opt',[raw,'-O3','-o',opt]); p.tool('wasm-validate',[opt])
            for kind,src in (('raw',raw),('O3',opt)):
                rows.append(dict(name=name,mode=mode,opt=kind,file=src.name,negative=False))
                if mode!='plain':
                    dst=out/f'{name}.{mode}.{kind}.recovered.wasm'
                    try:
                        stats=recover.recover(src,dst,accepted)
                        rows.append(dict(name=name,mode=mode+'-recovered',opt=kind,file=dst.name,negative=False))
                    except (ValueError,TimeoutError,OverflowError) as e:
                        stats=dict(status='timeout' if isinstance(e,TimeoutError) else 'unsupported',error=str(e))
                    analyses.append(dict(name=name,mode=mode,opt=kind,**stats))
                    p.save(out/'analysis.json',analyses)
        # A sign-flip kernel is valid Wasm and must fail both semantics and recognizer.
        body=p.kernel(p.payload(p.mix(p.matrix(p.source(plain)),221040)[1]))
        bad=body.replace('(call $det (local.get $n)))','(i32.sub (i32.const 0) (call $det (local.get $n))))')
        if bad==body: raise AssertionError('negative mutation missed')
        for kind in ('raw','O3'):
            dst=out/f'{name}.bad.{kind}.wasm'
            if kind=='raw': p.compile_wat(bad,dst)
            else: p.tool('wasm-opt',[out/f'{name}.bad.raw.wasm','-O3','-o',dst])
            p.tool('wasm-validate',[dst])
            rows.append(dict(name=name,mode='bad',opt=kind,file=dst.name,negative=True))
    p.save(out/'manifest.json',rows); p.save(out/'transforms.json',transforms)
    r=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=180)
    (out/'check.stdout.txt').write_text(r.stdout,encoding='utf-8'); (out/'check.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode: raise RuntimeError(r.stderr or r.stdout)
    pin(out); print(r.stdout)


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('output'); a=ap.parse_args(); run(a.output)
