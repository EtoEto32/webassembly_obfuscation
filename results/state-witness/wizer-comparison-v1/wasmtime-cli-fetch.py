"""Acquire the official fixed-version Wasmtime CLI for a direct Wizer comparison."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

TAG='v50.0.0'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'wasm-research-local-evidence'}),timeout=120) as response:
        return response.read()
def main(out):
    out.mkdir(parents=True,exist_ok=False)
    metadata=get(f'https://api.github.com/repos/bytecodealliance/wasmtime/releases/tags/{TAG}')
    release=json.loads(metadata)
    assert not release['prerelease'] and not release['draft'] and release['published_at'][:10]<='2026-10-25'
    expected=f'wasmtime-{TAG}-x86_64-windows.zip'
    asset=next(a for a in release['assets'] if a['name']==expected)
    raw=get(asset['browser_download_url']); digest=hashlib.sha256(raw).hexdigest()
    if asset.get('digest'): assert asset['digest']=='sha256:'+digest
    (out/'release.json').write_bytes(metadata)
    files=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for name in archive.namelist():
            if Path(name).name not in ('wasmtime.exe','LICENSE','README.md'): continue
            data=archive.read(name); dest=out/Path(name).name
            dest.write_bytes(data); files.append(dict(member=name,file=dest.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    assert (out/'wasmtime.exe').is_file()
    # Tie the inspected code to the release used, rather than silently mixing main and release.
    source_files=[]
    for name in ('lib.rs','rewrite.rs'):
        url=f'https://raw.githubusercontent.com/bytecodealliance/wasmtime/{TAG}/crates/wizer/src/{name}'
        data=get(url);dest=out/('wizer-'+name);dest.write_bytes(data)
        source_files.append(dict(url=url,file=dest.name,sha256=hashlib.sha256(data).hexdigest()))
    row=dict(tag=TAG,published=release['published_at'],url=asset['browser_download_url'],archiveBytes=len(raw),
             sha256=digest,publisherDigest=asset.get('digest'),files=files,source_files=source_files)
    (out/'provenance.json').write_text(json.dumps(row,indent=2))
    print(json.dumps(row))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('out',type=Path);main(parser.parse_args().out)
