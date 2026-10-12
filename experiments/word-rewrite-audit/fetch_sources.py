import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parent
tree=json.loads((ROOT.parents[1]/'tmp/local-mixing-source-audit/tree.json').read_text())
commit='5ce6daab669f50665f0c9aecf958f4066f407d01'
records=[]
for name in ['docs/local_mixing_documentation.md','src/engine/mixer/transformations.rs','src/engine/mixer/replacement.rs']:
    entry=next(x for x in tree['tree'] if x['path']==name)
    url='https://raw.githubusercontent.com/Local-Mixing/local_mixing/'+commit+'/'+name
    data=urllib.request.urlopen(url,timeout=20).read()
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert blob==entry['sha']
    filename=name.replace('/','__')
    with (ROOT/filename).open('xb') as output:
        output.write(data)
    records.append({'path':name,'url':url,'file':filename,'git_blob_sha1':blob,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
with (ROOT/'verified-sources.json').open('x',encoding='utf-8') as output:
    json.dump(records,output,indent=2)
print(json.dumps(records,indent=2))
