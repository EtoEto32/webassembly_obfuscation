"""Additional positive cases for XOR and repeated, nonconstant inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import prototype as p
import attack as a
from run import save,command,HERE

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    v=[('v',j) for j in [0,31,32,63,5,37,17,49]]
    ms={'xor4':('and',('xor',v[0],v[1]),('xor',v[2],v[3])),
        'active_repeat8':('xor',('and',('or',v[0],v[1]),('or',v[2],('not',v[0]))),('or',('and',v[3],v[4]),('and',v[5],('or',v[6],v[7]))))}
    files=[];analyses=[]
    def record(model,mode,level,path):files.append(dict(model=model,mode=mode,opt=level,path=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for name,t in ms.items():
        src=out/f'{name}.source.raw.wasm';p.c.compile_wat('(module (func (export "run") (param i32 i32) (result i32) '+p.formula_wat(t)+'))',src)
        bb=a.BDD();root=bb.source(t);assert root>0;canonical=bb.wasm(root)
        for mode in ('source','base','basis','fused','braid'):
            raw=out/f'{name}.{mode}.raw.wasm'
            if mode!='source':p.transform(src,raw,mode)
            for level in ('raw','O3'):
                path=raw if level=='raw' else out/f'{name}.{mode}.O3.wasm'
                if level=='O3':p.w.tool('wasm-opt',[raw,'-O3','--all-features','-o',path])
                record(name,mode,level,path)
                if mode!='source':
                    dst=out/f'{name}.{mode}.{level}.recovered.wasm';stats=a.recover(path,dst);assert dst.with_suffix('.wat').read_text()==canonical;analyses.append(dict(model=name,mode=mode,opt=level,**stats));record(name,mode+'.recovered',level,dst)
    save(out/'manifest.json',dict(models=ms,files=files));save(out/'analysis.json',analyses);save(out/'correctness.json',command(['node',HERE/'check.cjs',out]));print(json.dumps(dict(binaries=len(files),recovered=len(analyses))))

if __name__=='__main__':main()
