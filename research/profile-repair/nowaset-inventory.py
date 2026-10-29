"""Fetch only public provenance/tree metadata; never run artifact scripts."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

BASE='https://api.github.com/repos/michelledaviest/NodeWasmStudy'


def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'Wasm-Research-ReadOnly','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request,timeout=30) as response:
        data=response.read(8*1024*1024+1)
    if len(data)>8*1024*1024:raise ValueError('metadata size limit')
    return data


def main(out):
    if out.exists():raise FileExistsError(out)
    commit_bytes=fetch(BASE+'/commits/main');commit=json.loads(commit_bytes);sha=commit['sha']
    if len(sha)!=40 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('commit sha')
    tree_bytes=fetch(BASE+'/git/trees/'+sha+'?recursive=1');tree=json.loads(tree_bytes)
    if tree.get('truncated'):raise ValueError('truncated tree')
    blobs=[item for item in tree['tree'] if item['type']=='blob'];binaries=[b for b in blobs if b['path'].lower().endswith('.wasm')]
    report={'repository':'https://github.com/michelledaviest/NodeWasmStudy','commit':sha,'tree':tree['sha'],'wasmFiles':len(binaries),'wasmBytes':sum(b.get('size',0) for b in binaries),'files':binaries,'extensionCounts':dict(collections.Counter(Path(b['path']).suffix for b in blobs)),'note':'Read-only metadata; no project scripts or binaries executed.'}
    out.mkdir(parents=True);(out/'commit.json').write_bytes(commit_bytes);(out/'tree.json').write_bytes(tree_bytes);(out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf8');shutil.copy2(__file__,out/'nowaset-inventory.py')
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()},indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ('files','extensionCounts')}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);main(ap.parse_args().output.resolve())
