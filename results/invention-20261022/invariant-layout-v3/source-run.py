import argparse,json,shutil,struct,subprocess
from pathlib import Path
import prototype as p
import attack

NAMES=('mix','coupled','xor')
def source(name,pages=1):
    addr=lambda idx:f'(i32.add (i32.and (local.get 0) (i32.const -16)) (i32.shl (i32.and {idx} (i32.const 3)) (i32.const 2)))'
    index='(local.get 3)' if name!='coupled' else '(i32.add (local.get 3) (local.get 1))'
    a=addr(index);b=addr(f'(i32.add {index} (i32.const 1))')
    value={'mix':'(i32.xor (i32.rotl (i32.add (i32.add (local.get 4) (local.get 5)) (local.get 1)) (i32.const 7)) (i32.const 2654435769))',
           'coupled':'(i32.add (i32.mul (local.get 4) (i32.const 1664525)) (i32.xor (local.get 5) (local.get 1)))',
           'xor':'(i32.xor (i32.xor (local.get 4) (local.get 5)) (i32.add (local.get 1) (local.get 3)))'}[name]
    body=f'''(local.set 2 (i32.and (local.get 2) (i32.const 31)))
    (block $end (loop $next (br_if $end (i32.ge_u (local.get 3) (local.get 2)))
      (local.set 4 (i32.load {a})) (local.set 5 (i32.load {b}))
      (i32.store {b if name=='coupled' else a} {value})
      (local.set 3 (i32.add (local.get 3) (i32.const 1))) (br $next)))'''
    result=f'(i32.xor (i32.load {addr("(i32.const 0)")}) (i32.load {addr("(i32.const 3)")}))'
    data=bytes(64) if not pages else struct.pack('<16I',*[((i+1)*0x9e3779b1) & p.MASK for i in range(16)])
    seg='' if not pages else '(data (i32.const 0) "'+''.join('\\%02x'%b for b in data)+'")'
    return f'''(module (memory {pages} {pages}) {seg}
    (func (export "run") (param i32 i32 i32) (result i32) (local i32 i32 i32) {body} {result})
    (func (export "edge") (param i32 i32 i32) (result i32)
      (i32.store (i32.const 0) (local.get 1))
      (i32.store offset=4294967292 (i32.and (local.get 0) (i32.const -4)) (local.get 1)) (i32.const 0)))'''

def pin(out):
    for f in Path(__file__).parent.iterdir():
        if f.suffix in ('.py','.cjs'):shutil.copy2(f,out/('source-'+f.name))
    p.q.save(out/'pins.json',{str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file() and f.name!='pins.json'})

def run(output):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False);manifest=[];analyses=[];transforms=[]
    for name in NAMES:
        plain=out/f'{name}.plain.raw.wasm';p.q.compile(source(name),plain)
        for mode in ('plain','fixed','full','transport','bad'):
            raw=out/f'{name}.{mode}.raw.wasm'
            if mode!='plain':transforms.append(dict(name=name,**p.transform(plain,raw,mode)))
            opt=out/f'{name}.{mode}.O3.wasm';p.q.tool('wasm-opt',[raw,'--enable-simd','-O3','-o',opt])
            for kind,file in (('raw',raw),('O3',opt)):
                manifest.append(dict(name=name,mode=mode,opt=kind,file=file.name,negative=mode=='bad'))
                if mode!='plain':
                    dst=out/f'{name}.{mode}.{kind}.recovered.wasm'
                    try:
                        stats=attack.recover(file,dst,out/f'attack-{name}-{mode}-{kind}')
                        if mode=='bad':raise AssertionError('bad accepted')
                        manifest.append(dict(name=name,mode='recovered',opt=kind,file=dst.name,negative=False))
                    except (ValueError,RuntimeError) as exc:
                        stats=dict(status='rejected' if mode=='bad' else 'unsupported',error=str(exc))
                    analyses.append(dict(name=name,mode=mode,opt=kind,**stats))
                    p.q.save(out/'analysis.json',analyses)
    # Separate instrumentation artifacts expose memory for differential checks only.
    for row in manifest:
        m=p.q.read(out/row['file']);m.append(['export','"__physical"',['memory','0']])
        probe=out/(Path(row['file']).stem+'.probe.wasm');p.q.compile(p.sx.emit(m),probe);row['probe']=probe.name
    p.q.save(out/'manifest.json',manifest);p.q.save(out/'transforms.json',transforms)
    r=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=240)
    (out/'check.stdout.txt').write_text(r.stdout,encoding='utf8');(out/'check.stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr or r.stdout)
    pin(out);print(r.stdout)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');run(ap.parse_args().output)
