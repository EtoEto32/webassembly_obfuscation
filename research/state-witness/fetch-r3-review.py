"""Freeze public Wasm-R3-Bench metadata, then optionally download bounded binaries."""
import argparse,hashlib,json,urllib.request,urllib.parse
from pathlib import Path
REPO='doehyunbaek/wasm-benchmarks'
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'wasm-local-research'}),timeout=45).read()
def main(out,download=False):
    out.mkdir(parents=True,exist_ok=True);record=out/'inventory.json'
    if not record.exists():
        c=json.loads(get(f'https://api.github.com/repos/{REPO}/commits?until=2026-10-24T14:59:59Z&per_page=1'))[0]
        tree=json.loads(get(f'https://api.github.com/repos/{REPO}/git/trees/{c["sha"]}?recursive=1'));assert not tree.get('truncated')
        record.write_text(json.dumps({'repo':REPO,'commit':c['sha'],'date':c['commit']['committer']['date'],'tree':tree['tree']},indent=2))
    inv=json.loads(record.read_text());entries=[x for x in inv['tree'] if x['type']=='blob' and x['path'].startswith('wasm-r3-bench/') and x['path'].endswith('.wasm')]
    docs=[x for x in inv['tree'] if x['type']=='blob' and x['path'] in ('README.md','LICENSE','wasm-r3-bench/README.md','wasm-r3-bench/LICENSE')]
    chosen=list(docs);budget=32*1024*1024;skips=[]
    if download:
        for x in sorted(entries,key=lambda x:x['path']):
            if x['size']>4*1024*1024 or x['size']>budget:skips.append({'path':x['path'],'reason':'predeclared 4MiB/file or 32MiB aggregate download limit'});continue
            chosen.append(x);budget-=x['size']
    rows=[]
    for x in chosen:
        dest=out/x['path'];url=f'https://raw.githubusercontent.com/{REPO}/{inv["commit"]}/'+urllib.parse.quote(x['path'])
        if dest.exists():data=dest.read_bytes()
        else:data=get(url);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        assert len(data)==x['size'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==x['sha']
        rows.append({'path':x['path'],'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'gitBlob':x['sha']})
    target=out/('download.json' if download else 'docs.json')
    if target.exists():raise RuntimeError('Result already exists')
    target.write_text(json.dumps({'commit':inv['commit'],'rows':rows,'skips':skips},indent=2))
    print(json.dumps({'commit':inv['commit'],'date':inv['date'],'binaryCount':len(entries),'totalBytes':sum(x['size'] for x in entries),
                      'files':[{'path':x['path'],'bytes':x['size']} for x in entries],'downloadedFiles':len(rows),'skipped':len(skips)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--download',action='store_true');v=p.parse_args();main(v.out,v.download)
