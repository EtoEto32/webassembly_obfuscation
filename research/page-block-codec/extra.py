"""Add the high-address-first control, reusing the already tested source."""
import argparse, json, shutil, subprocess
from pathlib import Path
from run import p,q,HERE

def main(src,dst):
    src=Path(src);dst=Path(dst);dst.mkdir(parents=True,exist_ok=False);rows=[]
    for pages in (0,1,2):
        for suffix in ('.wasm','.probe.wasm'):
            f=src/f'p{pages}.plain.raw{suffix}';shutil.copyfile(f,dst/f.name)
        f=dst/f'p{pages}.block-high.raw.wasm';timing=p.transform(src/f'p{pages}.plain.raw.wasm',f,'block-high')
        for opt in ('raw','O3'):
            final=dst/f'p{pages}.block-high.{opt}.wasm'
            if opt=='O3':q.tool('wasm-opt',[f,'-O3','--enable-memory64','--enable-simd','--enable-sign-ext','-o',final]);q.w.tool('wasm-validate',[final])
            obs=dst/(final.stem+'.probe.wasm');p.probe(final,obs)
            rows.append(dict(pages=pages,mode='block-high',opt=opt,file=final.name,probe=obs.name,sha256=q.digest(final),bytes=final.stat().st_size,timing=timing))
    q.save(dst/'manifest.json',rows)
    r=subprocess.run(['node',str(HERE/'check.cjs'),str(dst),'--positive-only'],capture_output=True,text=True,timeout=120)
    (dst/'node.stdout.txt').write_text(r.stdout,encoding='utf-8');(dst/'node.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('output');a=ap.parse_args();main(a.source,a.output)
