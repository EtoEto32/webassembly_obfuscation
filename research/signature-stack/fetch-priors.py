"""Fetch public primary-source snapshots for local inspection, without executing them."""
import hashlib,json,urllib.request,sys
from pathlib import Path
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False)
SOURCES={
 'wasmparser-main-operators.rs':'https://raw.githubusercontent.com/bytecodealliance/wasm-tools/main/crates/wasmparser/src/validator/operators.rs',
 'wasmparser-262-operators.rs':'https://raw.githubusercontent.com/bytecodealliance/wasm-tools/v1.262.0/crates/wasmparser/src/validator/operators.rs',
 'v8-function-body-decoder-impl.h':'https://raw.githubusercontent.com/v8/v8/main/src/wasm/function-body-decoder-impl.h',
 'wasm-tools-2755.patch':'https://patch-diff.githubusercontent.com/raw/bytecodealliance/wasm-tools/pull/2755.patch',
 'wasm-tools-2726.patch':'https://patch-diff.githubusercontent.com/raw/bytecodealliance/wasm-tools/pull/2726.patch',
 'wabt-type-checker.cc':'https://raw.githubusercontent.com/WebAssembly/wabt/main/src/type-checker.cc',
}
records=[]
for name,url in SOURCES.items():
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-master-research/1.0'}),timeout=25) as r:data=r.read(2_000_000)
        p=OUT/name;p.write_bytes(data);records.append(dict(url=url,path=str(p.resolve()),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),status='downloaded'))
    except Exception as e:records.append(dict(url=url,status='unavailable',error=str(e)))
(OUT/'manifest.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
