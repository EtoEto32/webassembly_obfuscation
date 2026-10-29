"""Read-only upstream evidence collection at an explicit historical cutoff."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

REPO = 'bytecodealliance/wasmtime'
CUTOFF = '2026-10-25T00:00:00Z'
def get(url):
    request=urllib.request.Request(url, headers={'User-Agent':'wasm-research-local-evidence'})
    with urllib.request.urlopen(request, timeout=90) as response: return response.read()
def main(out):
    out.mkdir(parents=True, exist_ok=False)
    commits=json.loads(get(f'https://api.github.com/repos/{REPO}/commits?path=crates/wizer/src/lib.rs&until={CUTOFF}&per_page=1'))
    assert commits
    commit=commits[0]['sha']
    paths=['crates/wizer/src/'+name for name in ('lib.rs','parse.rs','rewrite.rs','instrument.rs','info.rs','snapshot.rs')]
    paths += ['crates/wizer/Cargo.toml']
    files=[]
    for path in paths:
        url=f'https://raw.githubusercontent.com/{REPO}/{commit}/{path}'
        data=get(url);dest=out/Path(path).name;dest.write_bytes(data)
        files.append(dict(path=path,file=dest.name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    (out/'provenance.json').write_text(json.dumps(dict(repo=REPO,cutoff=CUTOFF,commit=commit,
        committer=commits[0]['commit']['committer'],files=files),indent=2))
    print(json.dumps(dict(commit=commit,files=files)))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('out',type=Path);main(parser.parse_args().out)
