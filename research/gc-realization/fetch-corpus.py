"""Download a bounded, pinned set of benchmark binaries for STATIC inspection."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
def main(tree,out):
    meta=json.loads(tree.read_text());assert not meta.get('truncated');sha=meta['sha'];out.mkdir(parents=True,exist_ok=False);rows=[]
    selected=[r for r in meta['tree'] if r['path'].endswith('.wasm') and r['path'].split('/')[0] in ('benchmarks-out','interop-benchmarks-out','micro-benchmarks-out')]
    assert len(selected)<=12 and sum(r['size'] for r in selected)<20000000
    for r in selected:
        assert r['size']<6000000
        url='https://raw.githubusercontent.com/mkustermann/wasm_gc_benchmarks/'+sha+'/'+r['path']
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research/1.0'}),timeout=25) as response:data=response.read(6000001)
        assert len(data)==r['size'];blob=hashlib.sha1(('blob %d\0'%len(data)).encode()+data).hexdigest();assert blob==r['sha']
        file=r['path'].replace('/','__');(out/file).write_bytes(data);rows.append(dict(file=file,path=r['path'],url=url,commit=sha,blob_sha1=blob,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    (out/'manifest.json').write_text(json.dumps(rows,indent=2));print(json.dumps(dict(files=len(rows),bytes=sum(r['bytes'] for r in rows),commit=sha)))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('tree',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.tree,a.out)
