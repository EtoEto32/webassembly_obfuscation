"""Bounded read-only downloads of public primary implementation sources."""
import hashlib,json,sys,urllib.request
from pathlib import Path
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
sources={
 'binaryen-fuzzing.cpp':'https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/src/tools/fuzzing/fuzzing.cpp',
 'binaryen-heap-types.cpp':'https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/src/tools/fuzzing/heap-types.cpp',
 'smith-core.rs':'https://raw.githubusercontent.com/bytecodealliance/wasm-tools/v1.240.0/crates/wasm-smith/src/core.rs',
 'smith-code.rs':'https://raw.githubusercontent.com/bytecodealliance/wasm-tools/v1.240.0/crates/wasm-smith/src/core/code.rs',
}
rows=[]
for name,url in sources.items():
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-master-research/1.0'}),timeout=20) as r: data=r.read(2000001)
        if len(data)>2000000:raise ValueError('size bound')
        (out/name).write_bytes(data)
        rows.append(dict(file=name,url=url,status='downloaded',bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    except Exception as e:rows.append(dict(file=name,url=url,status='unavailable',error=str(e)))
(out/'manifest.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
