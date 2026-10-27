"""Expand a saved construction run to raw/O2/O3 without overwriting it."""
import json, subprocess, sys
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('rebasing',Path(__file__).with_name('compile.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
src,out=map(lambda p:Path(p).resolve(),sys.argv[1:3]);out.mkdir()
manifest=json.loads((src/'manifest.json').read_text());rows=[]
for a in manifest['artifacts']:
    original=src/a['file'];assert c.sha(original)==a['sha256']
    for level in ('raw','O2','O3'):
        target=out/(original.stem+'-'+level+'.wasm')
        if level=='raw':target.write_bytes(original.read_bytes())
        else:subprocess.run([str(c.wasm.TOOLS/'binaryen-version_133/bin/wasm-opt.exe'),str(original),'-'+level,'--enable-multivalue','-o',str(target)],capture_output=True,check=True,timeout=30)
        c.wasm.tool('wasm-validate',[target]);wat=c.wasm.tool('wasm2wat',[target,'--fold-exprs'])
        Path(str(target)+'.wat').write_text(wat,encoding='utf-8')
        tree=c.wasm.parse(wat)
        def nodes(n):
            if isinstance(n,list):
                yield n
                for v in n:yield from nodes(v)
        rows.append({**a,'level':level,'file':target.name,'bytes':target.stat().st_size,'sha256':c.sha(target),
                     'loads':sum(n[0]=='i32.load' for n in nodes(tree)),'loops':sum(n[0]=='loop' for n in nodes(tree))})
(out/'manifest.json').write_text(json.dumps({'artifacts':rows,'construction':str(src.relative_to(c.ROOT)),
   'optimizer':'Binaryen 133','note':'Residual loads/loops measure persistence only, not resistance.'},indent=2),encoding='utf-8')
(out/'optimize.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({'variants':len(rows)}))
