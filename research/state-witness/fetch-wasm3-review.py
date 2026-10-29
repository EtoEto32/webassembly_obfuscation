"""Download public source text for a dated prior-art review; execute none of it."""
import argparse,hashlib,json,urllib.request
from pathlib import Path

def main(out):
    out.mkdir(parents=True,exist_ok=True)
    if (out/'provenance.json').exists():raise RuntimeError('Review already fetched')
    def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'wasm-local-research'}),timeout=30).read()
    commit=json.loads(get('https://api.github.com/repos/wasm3/wasm3/commits?until=2026-10-24T14:59:59Z&per_page=1'))[0]
    sha=commit['sha'];rows=[]
    for name in ['docs/Testing.md','test/run-snapshot-test.py','test/run-snapshot-format-test.py','extra/pause-points.py']:
        url=f'https://raw.githubusercontent.com/wasm3/wasm3/{sha}/{name}'
        try:
            data=get(url);dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():raise RuntimeError('Refusing overwrite')
            dest.write_bytes(data);rows.append({'path':name,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
        except urllib.error.HTTPError as e:rows.append({'path':name,'url':url,'error':str(e)})
    result={'commit':sha,'commitDate':commit['commit']['committer']['date'],'rows':rows}
    (out/'provenance.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
