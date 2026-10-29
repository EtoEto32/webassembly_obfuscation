"""Fetch pinned upstream crate into the workspace; bounded safe tar extraction."""
import hashlib,json,sys,tarfile,urllib.request
from pathlib import Path,PurePosixPath
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=False)
url='https://static.crates.io/crates/wasm-smith/wasm-smith-0.262.0.crate'
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-master-research/1.0'}),timeout=25) as r:data=r.read(4000001)
assert len(data)<=4000000
archive=out/'wasm-smith-0.262.0.crate';archive.write_bytes(data)
records=[]
with tarfile.open(archive) as tf:
    members=tf.getmembers();assert sum(m.size for m in members)<=16000000
    for m in members:
        rel=PurePosixPath(m.name)
        if rel.is_absolute() or '..' in rel.parts or m.issym() or m.islnk():raise ValueError('unsafe tar path')
        dest=(out/str(rel)).resolve();dest.relative_to(out)
        if m.isdir():dest.mkdir(parents=True,exist_ok=True)
        elif m.isfile():
            dest.parent.mkdir(parents=True,exist_ok=True);content=tf.extractfile(m).read();dest.write_bytes(content)
            records.append(dict(file=str(dest.relative_to(out)),sha256=hashlib.sha256(content).hexdigest()))
        else:raise ValueError('unexpected tar member')
(out/'provenance.json').write_text(json.dumps(dict(url=url,archive_sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),files=records),indent=2))
print(json.dumps(dict(url=url,bytes=len(data),files=len(records),archive_sha256=hashlib.sha256(data).hexdigest())))
