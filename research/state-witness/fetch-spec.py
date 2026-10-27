"""Download public conformance sources; never execute downloaded JavaScript."""
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'.tools/state-witness-spec'
out.mkdir(parents=True,exist_ok=True)
def read(url,limit=2_000_000):
    request=urllib.request.Request(url,headers={'User-Agent':'Wasm-research-local-audit'})
    with urllib.request.urlopen(request,timeout=30) as response:data=response.read(limit+1)
    if len(data)>limit:raise ValueError('download size limit')
    return data
meta=json.loads(read('https://api.github.com/repos/WebAssembly/spec/commits?until=2026-10-24T23:59:59Z&per_page=1'))[0]
(out/'commit.json').write_text(json.dumps(meta,indent=2))
commit=meta['sha'];rows=[]
for name in ['memory_init.wast','table_init.wast']:
    url=f'https://raw.githubusercontent.com/WebAssembly/spec/{commit}/test/core/bulk-memory/{name}'
    data=read(url)
    if (out/name).exists():raise FileExistsError(out/name)
    (out/name).write_bytes(data)
    rows.append({'name':name,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
(out/'provenance.json').write_text(json.dumps({'commit':commit,'date':meta['commit']['committer']['date'],'rows':rows},indent=2))
print(json.dumps({'commit':commit,'files':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
