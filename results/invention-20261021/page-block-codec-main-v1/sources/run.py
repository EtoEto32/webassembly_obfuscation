import argparse, importlib.util, json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('page_proto',HERE/'prototype.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
q=p.q

def source(pages):
    out=[f'(module (memory {pages} {pages})']
    if pages:out.append('(data (i32.const 0) "'+''.join('\\%02x'%((i*37+19)&255) for i in range(64))+'")')
    for typ in ('i32','i64'):
        maxw=int(typ[1:])//8
        for w in (1,2,4,8):
            if w>maxw:continue
            for sign in ([''] if w==maxw else ['s','u']):
                op=typ+'.load'+(str(8*w)+'_'+sign if w<maxw else '')
                name=f'{typ}_ld{w}{sign}'
                out.append(f'(func (export "{name}") (param $a i32) (result {typ}) ({op} (local.get $a)))')
            op=typ+'.store'+(str(8*w) if w<maxw else '')
            out.append(f'(func (export "{typ}_st{w}") (param $a i32) (param $x {typ}) ({op} (local.get $a) (local.get $x)))')
    out.extend([
        '(func (export "offset_store") (param $a i32) (param $x i32) (i32.store offset=4294967292 (local.get $a) (local.get $x)))',
        '(func (export "offset_load") (param $a i32) (result i32) (i32.load offset=4294967292 (local.get $a)))',
        '(func $mark (param $p i32) (param $x i32) (result i32) (i32.store (i32.const 8) (local.get $x)) (local.get $p))',
        '(func $value (param $x i32) (result i32) (i32.store (i32.const 12) (local.get $x)) (local.get $x))',
        '(func (export "effects") (param $p i32) (param $x i32) (i32.store (call $mark (local.get $p) (local.get $x)) (call $value (i32.xor (local.get $x) (i32.const 123)))))',
        '(func (export "prefix") (param $p i32) (param $x i32) (i32.store (i32.const 4) (local.get $x)) (i64.store (local.get $p) (i64.extend_i32_u (local.get $x))))',
        '''(func (export "bench") (param $n i32) (param $off i32) (result i32)
        (local $i i32) (local $a i32) (local $x i32)
        (local.set $x (i32.const 1234567))
        (block $end (loop $loop
          (br_if $end (i32.ge_u (local.get $i) (local.get $n)))
          (local.set $a (i32.add (i32.add (i32.const 64) (i32.shl (i32.and (local.get $i) (i32.const 255)) (i32.const 5))) (local.get $off)))
          (local.set $x (i32.add (i32.rotl (local.get $x) (i32.const 7)) (local.get $i)))
          (i64.store (local.get $a) (i64.or (i64.extend_i32_u (local.get $x)) (i64.shl (i64.extend_i32_u (local.get $i)) (i64.const 32))))
          (local.set $x (i32.xor (local.get $x) (i32.load8_s (i32.add (local.get $a) (i32.const 3)))))
          (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $loop))) (local.get $x))''',')'])
    return '\n'.join(out)

def main(dst):
    dst=Path(dst);dst.mkdir(parents=True,exist_ok=False);rows=[]
    for pages in (0,1,2):
        raw=dst/f'p{pages}.plain.raw.wasm';q.compile(source(pages),raw)
        for mode in ('plain','lifted','byte','block','bad-partial','bad-wrap'):
            f=dst/f'p{pages}.{mode}.raw.wasm';timing={}
            if mode!='plain':timing=p.transform(raw,f,mode)
            for opt in ('raw','O3'):
                final=dst/f'p{pages}.{mode}.{opt}.wasm'
                if opt!='raw':q.tool('wasm-opt',[f,'-O3','--enable-memory64','--enable-simd','--enable-sign-ext','-o',final]);q.w.tool('wasm-validate',[final])
                obs=dst/(final.stem+'.probe.wasm');p.probe(final,obs)
                rows.append(dict(pages=pages,mode=mode,opt=opt,file=final.name,probe=obs.name,sha256=q.digest(final),bytes=final.stat().st_size,timing=timing))
    q.save(dst/'manifest.json',rows)
    r=subprocess.run(['node',str(HERE/'check.cjs'),str(dst)],capture_output=True,text=True,timeout=120)
    (dst/'node.stdout.txt').write_text(r.stdout,encoding='utf-8');(dst/'node.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();main(a.output)
