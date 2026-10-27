import argparse,json
from pathlib import Path
import prototype as q
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=[]
    src=out/'source.wasm';q.compile(q.source_text(('add',0,1)),src)
    for mode in ('plain','decode','table'):
        f=out/(mode+'.wasm');q.transform(src,f,mode,7)
        for opt in ('raw','O3'):
            g=f if opt=='raw' else out/(mode+'-O3.wasm')
            if opt=='O3':q.tool('wasm-opt',[f,'-O3','--enable-simd','-o',g])
            try:r=q.lower(g,out/(mode+'-'+opt+'-recovered.wasm'));r['status']='ok'
            except Exception as e:r=dict(status='error',error=type(e).__name__,message=str(e))
            r.update(mode=mode,opt=opt);rows.append(r)
    q.save(out/'probe.json',rows);print(json.dumps(rows))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');main(a.parse_args().output)
