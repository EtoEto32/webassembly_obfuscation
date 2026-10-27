"""Fetch a fixed official release, verify its published checksum, extract only wasm-opt."""
import hashlib,json,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/heap-observer/history-release-v1';DEST=ROOT/'.tools/heap-observer-binaryen-123'
def fetch(url,cap):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research/1.0'}),timeout=45) as r:data=r.read(cap+1)
 if len(data)>cap:raise ValueError('size cap')
 return data
def main():
 release=json.loads((OUT/'release.json').read_text(encoding='utf8'));name='binaryen-version_123-x86_64-windows.tar.gz';assets={a['name']:a for a in release['assets']}
 checksum=fetch(assets[name+'.sha256']['browser_download_url'],1024);(OUT/(name+'.sha256')).write_bytes(checksum);expected=checksum.decode().split()[0]
 data=fetch(assets[name]['browser_download_url'],80000000);actual=hashlib.sha256(data).hexdigest()
 if actual!=expected:raise ValueError('published checksum mismatch')
 archive=OUT/name;archive.write_bytes(data);DEST.mkdir(parents=True,exist_ok=False)
 with tarfile.open(archive,'r:gz') as tar:
  member=tar.getmember('binaryen-version_123/bin/wasm-opt.exe')
  if not member.isfile() or member.size>100000000:raise ValueError('unexpected archive entry')
  body=tar.extractfile(member).read();(DEST/'wasm-opt.exe').write_bytes(body)
 report=dict(release=release['html_url'],published=release['published_at'],url=assets[name]['browser_download_url'],archive_bytes=len(data),archive_sha256=actual,published_sha256=expected,executable=str(DEST/'wasm-opt.exe'),executable_sha256=hashlib.sha256(body).hexdigest())
 (OUT/'download.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
