import hashlib,json,sys,urllib.request
from pathlib import Path
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-master-research/1.0'}),timeout=30) as r:return r.read(2_000_000)
sha='aa4dcf44b8de3f3f3270ca067422172518ecc341'
api=f'https://api.github.com/repos/WebAssembly/spec/commits/{sha}'
commit=fetch(api);(out/'commit.json').write_bytes(commit);assert json.loads(commit)['sha']==sha
records=[]
for name in ['block','loop','if','br','br_if','br_table','return','call','select','unreachable','local_get','local_set','local_tee']:
    url=f'https://raw.githubusercontent.com/WebAssembly/spec/{sha}/test/core/{name}.wast';data=fetch(url)
    p=out/(name+'.wast');p.write_bytes(data);records.append(dict(url=url,path=str(p.resolve()),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
(out/'manifest.json').write_text(json.dumps(dict(commit=sha,api=api,files=records),indent=2));print(json.dumps(dict(commit=sha,files=len(records))))
