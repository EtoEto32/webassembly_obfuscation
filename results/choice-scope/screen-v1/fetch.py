"""Download bounded public primary sources for reading; never execute them."""
import hashlib,json,sys,urllib.request
from pathlib import Path
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
sha='aa4dcf44b8de3f3f3270ca067422172518ecc341'
sources={
 'numerics.rst':f'https://raw.githubusercontent.com/WebAssembly/spec/{sha}/document/core/exec/numerics.rst',
 'binaryen-8676.patch':'https://patch-diff.githubusercontent.com/raw/WebAssembly/binaryen/pull/8676.patch',
 'binaryen-fuzz_opt.py':'https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/scripts/fuzz_opt.py',
 'spec-relaxed-laneselect.wast':f'https://raw.githubusercontent.com/WebAssembly/spec/{sha}/test/core/relaxed-simd/relaxed_laneselect.wast',
}
rows=[]
for name,url in sources.items():
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-master-research/1.0'}),timeout=25) as r: data=r.read(2_000_001)
        if len(data)>2_000_000: raise ValueError('size limit')
        (out/name).write_bytes(data)
        rows.append(dict(file=name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),status='downloaded'))
    except Exception as e: rows.append(dict(file=name,url=url,status='unavailable',error=str(e)))
(out/'manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf8');print(json.dumps(rows,indent=2))
