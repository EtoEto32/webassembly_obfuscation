"""Build fixed experiment matrix; refuses existing output."""
import json,subprocess,sys
from pathlib import Path
import prototype as p
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
for profile in ('full','counter'):
    src=out/(profile+'-source.wasm');p.compile(p.fixture(profile=='counter'),src)
    modes=['plain','native-neg','cas-neg','cas-affine']+(['native-affine','bad-split'] if profile=='counter' else ['bad-and'])
    for mode in modes:
        raw=out/(profile+'-'+mode+'-raw.wasm');meta=p.transform(src,raw,mode)
        for opt in ('raw','O3'):
            f=raw if opt=='raw' else out/(profile+'-'+mode+'-O3.wasm')
            if opt=='O3':p.q.tool('wasm-opt',[raw,'-O3','--enable-threads','-o',f]);p.q.w.tool('wasm-validate',[f,'--enable-threads'])
            rows.append(dict(**{**meta,'bytes':f.stat().st_size},profile=profile,opt=opt,file=f.name,sha256=p.q.digest(f),negative=mode.startswith('bad')))
(out/'manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=120)
print(json.dumps(dict(binaries=len(rows),out=str(out))))
