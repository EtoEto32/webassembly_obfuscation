"""Bounded download of primary references; never executes downloaded code."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for name,url in {
        'mad-eye.pdf':'https://peng-hui.github.io/data/paper/icse26%3Amad-eye.pdf',
        'binaryen-fuzzing.cpp':'https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/src/tools/fuzzing/fuzzing.cpp',
        'binaryen-heap-types.cpp':'https://raw.githubusercontent.com/WebAssembly/binaryen/version_133/src/tools/fuzzing/heap-types.cpp',
        'rr-reduce.html':'https://arxiv.org/html/2506.07834v2',
        'genwasym.html':'https://arxiv.org/html/2608.18327v2'
    }.items():
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research/1.0'}),timeout=25) as r:data=r.read(5000001)
            if len(data)>5000000:raise ValueError('size cap')
            (out/name).write_bytes(data);rows.append(dict(file=name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),status='downloaded'))
        except Exception as e:rows.append(dict(file=name,url=url,status='unavailable',error=str(e)))
    (out/'manifest.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
