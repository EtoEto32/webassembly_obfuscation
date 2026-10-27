"""Pinned public Weave core/transform sources; no upstream scripts executed."""
import argparse,concurrent.futures,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
a=argparse.ArgumentParser();a.add_argument('--out',type=Path,default=ROOT/'.tools/weave-build');out=a.parse_args().out
out.mkdir(parents=True,exist_ok=False);commit='55e36b5f5d5b31d14f1521c3a4327c248ddeba19'
url=f'https://api.github.com/repos/dphilla/weave/git/trees/{commit}?recursive=1'
request=urllib.request.Request(url,headers={'User-Agent':'Wasm-research-local-audit'})
with urllib.request.urlopen(request,timeout=30) as r:raw=r.read(20_000_001)
assert len(raw)<=20_000_000
info=json.loads(raw);assert not info.get('truncated');tree=info['tree']
(out/'source-tree.json').write_bytes(raw)
names={'Cargo.toml','Cargo.lock','LICENSE','crates/weave-core/Cargo.toml','crates/weave-transform/Cargo.toml','js/weave.mjs'}
selected=[x for x in tree if x['type']=='blob' and (x['path'].startswith(('crates/weave-core/src/','crates/weave-transform/src/')) or x['path'] in names)]
assert len(selected)==20
def fetch(x):
    name=x['path'];local='.upstream/'+name if name in ('Cargo.toml','Cargo.lock') else name
    url=f'https://raw.githubusercontent.com/dphilla/weave/{commit}/{name}'
    data=urllib.request.urlopen(url,timeout=30).read(2_000_001);assert len(data)<=2_000_000
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==x['sha']
    p=out/local;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    return {'path':name,'localPath':local,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'gitBlob':x['sha']}
rows=[]
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(fetch,selected):rows.append(row)
finally:(out/'provenance.json').write_text(json.dumps({'commit':commit,'rows':rows},indent=2))
print(json.dumps({'files':len(rows),'bytes':sum(x['size'] for x in selected)}))
