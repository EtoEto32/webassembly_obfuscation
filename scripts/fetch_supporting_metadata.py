"""Fetch small author files pinned to previously audited Git commits."""
import hashlib
import json
from acquire import ROOT, get


def main():
    requests=[('minerray','Data/HashingSiteResultSamples.csv'),('minerray','Data/sites.csv'),
              ('wasmizer','LICENSE'),('minesweeper','LICENSE')]
    results=[]
    for dataset,source_path in requests:
        base=ROOT/'data/catalog'/dataset
        tree=json.loads((base/'tree.json').read_text(encoding='utf-8'))
        repo=json.loads((base/'repository.json').read_text(encoding='utf-8'))
        entry=next(r for r in tree['tree'] if r['path']==source_path)
        url=f"https://raw.githubusercontent.com/{repo['full_name']}/{tree['sha']}/{source_path}"
        dest=base/'supporting'/source_path;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():
            with get(url) as response:raw=response.read()
            actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if actual!=entry['sha']:raise ValueError('Git blob mismatch')
            dest.write_bytes(raw)
        raw=dest.read_bytes()
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual!=entry['sha']:raise ValueError('cached Git blob mismatch')
        row={'dataset':dataset,'source_path':source_path,'commit':tree['sha'],'git_blob':actual,'url':url,
             'local_path':dest.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        results.append(row);print(json.dumps(row),flush=True)
    (ROOT/'results/catalog/supporting-metadata-receipts.json').write_text(json.dumps(results,indent=2),encoding='utf-8')


if __name__=='__main__':main()
