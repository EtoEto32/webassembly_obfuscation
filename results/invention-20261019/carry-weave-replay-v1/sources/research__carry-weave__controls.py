import argparse,json,subprocess
from pathlib import Path
import prototype as p
import run
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=[]
    for n in (4,5,7,128):
        m,spec=run.source(n,0);src=out/f'n{n}-source.wasm';p.compile(p.w.emit(m),src);truth=p.recover(src)['terms']
        for mode in ('plain','packed','csa','splitadd','splitcsa'):
            raw=out/f'n{n}-{mode}-raw.wasm';info=p.transform(src,raw,mode)
            for opt in ('raw','O3'):
                f=raw if opt=='raw' else out/f'n{n}-{mode}-O3.wasm'
                if opt=='O3':p.tool('wasm-opt',[raw,'--enable-simd','-O3','-o',f])
                rec=out/(f.stem+'-recovered.wasm');a=p.recover(f,rec);rows.append(dict(info,n=n,kind=0,spec=spec,opt=opt,source=src.name,file=f.name,recovered=rec.name,sha256=p.digest(f),recovered_sha256=p.digest(rec),term_match=a['terms']==truth,attack=a))
    p.save(out/'manifest.json',rows);p.save(out/'negative-manifest.json',[])
    subprocess.run(['node',str(Path(__file__).parent/'check.cjs'),str(out)],check=True,timeout=120)
    refusals=[]
    for n in (3,129):
        src=out/f'n{n}-refuse.wasm';p.compile(p.w.emit(run.source(n,0)[0]),src)
        try:p.transform(src,out/f'n{n}-unexpected.wasm')
        except p.Unsupported as e:refusals.append(dict(terms=n,reason=str(e)))
        else:raise AssertionError(n)
    p.save(out/'summary.json',dict(targets=len(rows),term_matches=sum(r['term_match'] for r in rows),refusals=refusals,**json.loads((out/'checks.json').read_text())));print((out/'summary.json').read_text())
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
