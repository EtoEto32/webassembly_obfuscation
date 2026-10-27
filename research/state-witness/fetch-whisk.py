"""Read-only public-source acquisition for a pinned Whisk comparison."""
import argparse,hashlib,json,urllib.request
from pathlib import Path

def get(url,limit=8000000):
    req=urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research-prior-art-review'})
    with urllib.request.urlopen(req,timeout=30) as r:data=r.read(limit+1)
    if len(data)>limit:raise ValueError('download limit')
    return data

def main(out):
    out.mkdir(parents=True,exist_ok=False);repo='nokia-steward/web-assembly-self-certifying-compilation-framework';api='https://api.github.com/repos/'+repo
    raw=get(api+'/commits?until=2026-10-24T00:00:00Z&per_page=1');(out/'commit.json').write_bytes(raw);commit=json.loads(raw)[0]['sha']
    raw=get(api+'/git/trees/'+commit+'?recursive=1');(out/'tree.json').write_bytes(raw);info=json.loads(raw);assert not info.get('truncated')
    names={x['path']:x for x in info['tree'] if x['type']=='blob'}
    # Documentation first; no downloaded script or project code is executed.
    selected=[x for x in names if x.lower() in ('readme.md','license','license.txt','makefile','.gitmodules','dune-project')]
    rows=[]
    for name in selected:
        url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+name;data=get(url,1000000)
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==names[name]['sha']
        (out/name).write_bytes(data);rows.append({'path':name,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'gitBlob':names[name]['sha']})
    (out/'provenance.json').write_text(json.dumps({'repository':repo,'commit':commit,'rows':rows},indent=2))
    print(json.dumps({'commit':commit,'downloaded':selected,'paths':[x for x in names if x.endswith(('.ml','.mli','.opam')) or 'dune' in x][:100]}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
