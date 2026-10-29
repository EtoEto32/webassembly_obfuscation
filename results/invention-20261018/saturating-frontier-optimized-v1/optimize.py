"""Save raw/O2/O3 artifacts and reference expressions; never overwrite a run."""
import importlib.util,json,subprocess,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('sf',Path(__file__).with_name('compile.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
src,out=map(Path,sys.argv[1:3]);out.mkdir();m=json.loads((src/'manifest.json').read_text());rows=[]
for a in m['artifacts']:
    p=src/a['file'];assert c.sha(p)==a['sha256']
    for level in ('raw','O2','O3'):
        dst=out/(p.stem+'-'+level+'.wasm')
        if level=='raw':dst.write_bytes(p.read_bytes())
        else:subprocess.run([str(c.wasm.TOOLS/'binaryen-version_133/bin/wasm-opt.exe'),str(p),'-'+level,'--enable-simd','-o',str(dst)],check=True,capture_output=True,timeout=30)
        c.wasm.tool('wasm-validate',[dst]);wat=c.wasm.tool('wasm2wat',[dst,'--fold-exprs']);Path(str(dst)+'.wat').write_text(wat,encoding='utf-8')
        rows.append({**a,'level':level,'file':dst.name,'sha256':c.sha(dst),'bytes':dst.stat().st_size,
                     'satAddInstructions':wat.count('i16x8.add_sat_u'),'minInstructions':wat.count('i16x8.min_u')})
(out/'manifest.json').write_text(json.dumps({'artifacts':rows,'referenceExpressions':m['referenceExpressions'],'construction':str(src),'optimizer':'Binaryen 133'},indent=2),encoding='utf-8')
(out/'optimize.py').write_bytes(Path(__file__).read_bytes());print({'variants':len(rows)})
