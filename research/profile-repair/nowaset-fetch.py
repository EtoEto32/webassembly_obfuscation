"""Bounded read-only download of pinned public Wasm blobs, deduplicated by git ID."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request


def blob_id(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def main(inventory,out):
    meta=json.loads((inventory/'results.json').read_text(encoding='utf8'))
    unique={}
    for item in meta['files']:
        if item['path'].startswith('data/dumped-wasm-files/'):unique.setdefault(item['sha'],item)
    items=sorted(unique.values(),key=lambda x:x['sha'])
    if len(items)>300 or sum(r['size'] for r in items)>128*1024*1024 or any(r['size']>32*1024*1024 for r in items):raise ValueError('download budget')
    out.mkdir(parents=True,exist_ok=True)
    def fetch(item):
        sha=item['sha']
        if len(sha)!=40 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('blob ID')
        file=out/(sha+'.wasm')
        url='https://raw.githubusercontent.com/michelledaviest/NodeWasmStudy/'+meta['commit']+'/'+urllib.parse.quote(item['path'],safe='/')
        if file.exists():data=file.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-Research-ReadOnly'}),timeout=30) as response:data=response.read(item['size']+1)
        if len(data)!=item['size'] or blob_id(data)!=sha:raise ValueError('blob mismatch '+sha)
        if not file.exists():file.write_bytes(data)
        return {'file':file.name,'sourcePath':item['path'],'sourceURL':url,'gitBlob':sha,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:files=list(pool.map(fetch,items))
    report={'repository':meta['repository'],'commit':meta['commit'],'files':files,'totalBytes':sum(r['bytes'] for r in files),'note':'Only immutable public binary data fetched; no Wasm or package scripts executed. Git blob IDs and SHA256 recorded.'}
    (out/'provenance.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'files':len(files),'bytes':report['totalBytes'],'directory':str(out)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('inventory',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.inventory.resolve(),a.output.resolve())
