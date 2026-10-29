"""Fetch a bounded, pinned upstream library subset for an external comparison."""
import argparse,concurrent.futures,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--out',type=Path,default=ROOT/'.tools/wasm-migrate-build')
out=a.parse_args().out;out.mkdir(parents=True,exist_ok=False)
commit='e28a37cd2c00f0f5026bbc79651a50cbea6172dd'
url=f'https://api.github.com/repos/TintoEdoardo/wasm-tools/git/trees/{commit}?recursive=1'
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-research-local-audit'}),timeout=30) as r:raw=r.read(20_000_001)
assert len(raw)<=20_000_000
treeinfo=json.loads(raw);assert not treeinfo.get('truncated');tree=treeinfo['tree']
(out/'source-tree.json').write_bytes(raw)
names={'wasm-migrate','wasm-mutate','wasmparser','wasm-encoder','wasmprinter','wat','wast'}
selected=[x for x in tree if x['type']=='blob' and len(x['path'].split('/'))>=3 and x['path'].split('/')[0]=='crates'
          and x['path'].split('/')[1] in names and (x['path'].split('/')[2]=='src' or x['path'].split('/')[-1] in ['Cargo.toml','build.rs'])]
assert len(selected)<500 and sum(x['size'] for x in selected)<10_000_000
extras={'Cargo.toml','Cargo.lock','crates/wasmparser/benches/benchmark.rs','crates/wast/tests/parse-fail.rs',
        'LICENSE-APACHE','LICENSE-MIT','LICENSE-Apache-2.0_WITH_LLVM-exception'}
selected.extend(x for x in tree if x['type']=='blob' and x['path'] in extras)
assert len({x['path'] for x in selected})==len(selected)
rows=[]
def fetch(item):
    name=item['path'];local=('.upstream/'+name) if name in ('Cargo.toml','Cargo.lock') else name
    dest=out/local;dest.resolve().relative_to(out.resolve());dest.parent.mkdir(parents=True,exist_ok=True)
    url=f'https://raw.githubusercontent.com/TintoEdoardo/wasm-tools/{commit}/{name}'
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-research-local-audit'}),timeout=30) as r:data=r.read(2_000_001)
    if len(data)>2_000_000:raise ValueError('file too large')
    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=item['sha']:raise ValueError('Git blob mismatch')
    dest.write_bytes(data)
    return {'path':name,'localPath':local,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'gitBlob':item['sha']}
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(fetch,selected):rows.append(row)
finally:
    (out/'provenance.json').write_text(json.dumps({'commit':commit,'rows':rows},indent=2))
print(json.dumps({'files':len(rows),'bytes':sum(x['size'] for x in selected)}))
