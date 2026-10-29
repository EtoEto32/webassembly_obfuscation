import json,platform,subprocess,sys
from pathlib import Path
import prototype as p
def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);q=p.q;rows=[]
    env=json.loads(subprocess.check_output(['node','-e','console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require("os").cpus()[0].model,logical_cpus:require("os").cpus().length}))'],text=True))
    q.save(out/'environment.json',dict(python=platform.python_version(),os=platform.platform(),wabt=q.w.tool('wat2wasm',['--version']).strip(),binaryen=q.tool('wasm-opt',['--version']).strip(),**env))
    for n in (256,4096):
        src=out/f'n{n}-source.wasm';q.compile(p.build(n),src)
        for mode in p.MODES:
            for seed in ((0,) if mode in ('plain','complement') else (7,29)):
                raw=out/f'n{n}-{mode}-s{seed}-raw.wasm';info=p.transform(src,raw,mode,seed)
                for opt in ('raw','O3'):
                    f=raw if opt=='raw' else out/(raw.stem.replace('-raw','-O3')+'.wasm')
                    if opt=='O3':q.tool('wasm-opt',[raw,'--enable-simd','--enable-relaxed-simd','--enable-bulk-memory','-O3','-o',f])
                    m=q.read(f);obs=out/(f.stem+'-observe.wasm');m.append(['export','"memory"',['memory','0']]);q.compile(q.w.emit(m),obs)
                    rows.append(dict(info,opt=opt,file=f.name,observed=obs.name,source=src.name,sha256=q.digest(f),bytes=f.stat().st_size))
        q.save(out/'manifest.json',rows)
    subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=180)
    print(json.dumps(dict(targets=len(rows),checks={k:v for k,v in json.loads((out/'checks.json').read_text()).items() if k!='records'})))
if __name__=='__main__':main(sys.argv[1])
