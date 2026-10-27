"""Read public history and reference implementation to resolve a model mismatch."""
import hashlib,json,sys,urllib.request
from pathlib import Path
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);rows=[]
def fetch(name,url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-master-research/1.0'}),timeout=25) as r:data=r.read(2000001)
        if len(data)>2000000:raise ValueError('size cap')
        (out/name).write_bytes(data);rows.append(dict(file=name,url=url,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),status='downloaded'));return data
    except Exception as e:rows.append(dict(file=name,url=url,status='unavailable',error=str(e)))
sha='aa4dcf44b8de3f3f3270ca067422172518ecc341'
fetch('issue125.json','https://api.github.com/repos/WebAssembly/relaxed-simd/issues/125')
fetch('issue125-comments.json','https://api.github.com/repos/WebAssembly/relaxed-simd/issues/125/comments?per_page=100')
fetch('fix-laneselect.patch','https://github.com/WebAssembly/relaxed-simd/commit/2fd9172.patch')
tree=fetch('spec-tree.json',f'https://api.github.com/repos/WebAssembly/spec/git/trees/{sha}?recursive=1')
if tree:
    paths=[r['path'] for r in json.loads(tree)['tree'] if r['path'].startswith('interpreter/') and r['path'].endswith('.ml') and any(s in r['path'] for s in ('numeric','eval','i8x16','i16x8','i32x4','i64x2'))]
    for path in paths[:16]:fetch(path.replace('/','-'),f'https://raw.githubusercontent.com/WebAssembly/spec/{sha}/{path}')
(out/'manifest.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
