"""Read pinned public references/metadata; no downloaded code is executed."""
import argparse,hashlib,json,urllib.request
from pathlib import Path

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    sources={
      'korat.pdf':'https://users.ece.utexas.edu/~khurshid/testera/korat.pdf',
      'binaryen-fuzz-opt.py':'https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/scripts/fuzz_opt.py',
      'dart-tree.json':'https://api.github.com/repos/mkustermann/wasm_gc_benchmarks/git/trees/main?recursive=1',
      'dart-readme.md':'https://raw.githubusercontent.com/mkustermann/wasm_gc_benchmarks/main/README.md',
      'spec-aggregate.rst':'https://raw.githubusercontent.com/WebAssembly/spec/main/document/core/exec/instructions.rst',
    }
    for name,url in sources.items():
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research/1.0'}),timeout=25) as r:data=r.read(3000001)
            if len(data)>3000000:raise ValueError('size cap')
            (out/name).write_bytes(data);rows.append(dict(file=name,url=url,status='downloaded',bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        except Exception as e:rows.append(dict(file=name,url=url,status='unavailable',error=str(e)))
    (out/'manifest.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
