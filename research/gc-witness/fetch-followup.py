"""Version/near-prior check; download only, do not execute external sources."""
import hashlib,json,sys,urllib.request
from pathlib import Path
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
sources={
 'binaryen-9282.patch':'https://patch-diff.githubusercontent.com/raw/WebAssembly/binaryen/pull/9282.patch',
 'binaryen-9282.json':'https://api.github.com/repos/WebAssembly/binaryen/pulls/9282',
 'smith-core-262.rs':'https://raw.githubusercontent.com/bytecodealliance/wasm-tools/v1.262.0/crates/wasm-smith/src/core.rs',
 'smith-code-builder-262.rs':'https://raw.githubusercontent.com/bytecodealliance/wasm-tools/v1.262.0/crates/wasm-smith/src/core/code_builder.rs',
 'binaryen-main-commit.json':'https://api.github.com/repos/WebAssembly/binaryen/commits/main',
 'binaryen-main-heap-types.cpp':'https://raw.githubusercontent.com/WebAssembly/binaryen/main/src/tools/fuzzing/heap-types.cpp',
}
rows=[]
for name,url in sources.items():
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-master-research/1.0'}),timeout=20) as r:data=r.read(2000001)
        if len(data)>2000000:raise ValueError('size bound')
        (out/name).write_bytes(data);rows.append(dict(file=name,url=url,status='downloaded',bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    except Exception as e:rows.append(dict(file=name,url=url,status='unavailable',error=str(e)))
(out/'manifest.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
