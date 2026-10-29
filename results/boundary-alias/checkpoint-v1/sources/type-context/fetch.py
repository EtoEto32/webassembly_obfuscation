"""Bounded read-only fetch of closest upstream type-test sources."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for name,url in {
        'wasm-fuzz-types.cpp':'https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/src/tools/wasm-fuzz-types.cpp',
        'wasm-type.cpp':'https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/test/gtest/wasm-type.cpp',
        'fuzz_shell.js':'https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/scripts/fuzz_shell.js',
        'type-rec.wast':'https://raw.githubusercontent.com/WebAssembly/testsuite/main/type-rec.wast',
        'canonical-types-unittest.cc':'https://raw.githubusercontent.com/v8/v8/main/test/unittests/wasm/canonical-types-unittest.cc',
    }.items():
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research/1.0'}),timeout=25) as r:data=r.read(2000001)
            if len(data)>2000000:raise ValueError('size cap')
            (out/name).write_bytes(data);rows.append(dict(file=name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),status='downloaded'))
        except Exception as e:rows.append(dict(file=name,url=url,status='unavailable',error=str(e)))
    (out/'manifest.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
