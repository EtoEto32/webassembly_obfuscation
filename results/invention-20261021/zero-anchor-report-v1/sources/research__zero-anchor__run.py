import json, platform, subprocess, sys
from pathlib import Path
import prototype as p

MODELS = {
    'add1': [('add',1,0)],
    'sub1': [('sub',1,0)],
    'add8': [('add',1,i) for i in range(8)],
    'add32': [('add',1+(i//8)%2,i%8) for i in range(32)],
    'mixed8': [(('add','sub','xor')[i%3],1+i%2,i%8) for i in range(8)],
    'xor8': [('xor',1,i) for i in range(8)],
}
def main(out):
    out=Path(out); out.mkdir(parents=True,exist_ok=False); q=p.q
    q.save(out/'models.json',MODELS)
    env=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require("os").cpus()[0].model,logical_cpus:require("os").cpus().length}))'],text=True))
    q.save(out/'environment.json',dict(python=platform.python_version(),os=platform.platform(),binaryen=q.tool('wasm-opt',['--version']).strip(),wabt=q.w.tool('wat2wasm',['--version']).strip(),**env))
    rows=[]
    for name,steps in MODELS.items():
        src=out/(name+'-source.wasm');q.compile(p.source(steps),src)
        for mode in p.MODES:
            for seed in ((0,) if mode=='plain' else (7,29)):
                raw=out/f'{name}-{mode}-s{seed}-raw.wasm';info=p.transform(src,raw,mode,seed)
                for opt in ('raw','O3'):
                    f=raw if opt=='raw' else out/(raw.stem.replace('-raw','-O3')+'.wasm')
                    if opt=='O3': q.tool('wasm-opt',[raw,'--enable-simd','--enable-relaxed-simd','-O3','-o',f])
                    m=q.read(f); counts={}
                    for e in q.walk(m): counts[e[0]]=counts.get(e[0],0)+1
                    rows.append(dict(info,kernel=name,opt=opt,file=f.name,source=src.name,sha256=q.digest(f),bytes=f.stat().st_size,instructions=counts))
        q.save(out/'manifest.json',rows)
    subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=120)
    print(json.dumps(dict(targets=len(rows),checks=json.loads((out/'checks.json').read_text()))))
if __name__=='__main__': main(sys.argv[1])
