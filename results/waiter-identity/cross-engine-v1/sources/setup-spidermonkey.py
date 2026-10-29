"""Fetch a pinned official JS shell into the workspace; no system install."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.tools/spidermonkey-150.0.1'
BASE='https://archive.mozilla.org/pub/firefox/releases/150.0.1/'
ARCHIVE='jsshell/jsshell-win64.zip'


def get(url,limit):
    with urllib.request.urlopen(url,timeout=45) as r:data=r.read(limit+1)
    if len(data)>limit:raise ValueError('size bound')
    return data


def main():
    if OUT.exists():
        record=json.loads((OUT/'provenance.json').read_text())
        for name,value in record['files'].items():assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==value
        print(json.dumps(record));return
    checksums=get(BASE+'SHA512SUMS',4*1024*1024)
    candidates=[line.split()[0] for line in checksums.decode().splitlines() if line.split()[-1]==ARCHIVE]
    if len(candidates)!=1:raise ValueError('checksum record missing or ambiguous')
    data=get(BASE+ARCHIVE,32*1024*1024)
    if hashlib.sha512(data).hexdigest()!=candidates[0]:raise ValueError('official checksum mismatch')
    entries=[];size=0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            if info.is_dir():continue
            dest=(OUT/info.filename).resolve()
            if OUT.resolve() not in dest.parents:raise ValueError('archive path')
            if (info.external_attr>>16)&0o170000==0o120000:raise ValueError('archive symlink')
            size+=info.file_size
            if size>128*1024*1024:raise ValueError('unpacked size bound')
            entries.append((dest,z.read(info)))
    OUT.mkdir(parents=True,exist_ok=False)
    for dest,content in entries:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
    (OUT/'archive.zip').write_bytes(data);(OUT/'SHA512SUMS').write_bytes(checksums)
    record={'version':'150.0.1','url':BASE+ARCHIVE,'checksumUrl':BASE+'SHA512SUMS','sha512':candidates[0],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'files':{str(p.relative_to(OUT)):hashlib.sha256(content).hexdigest() for p,content in entries},'note':'Official HTTPS archive and same-channel checksum; no system installation, detached signature not independently verified.'}
    (OUT/'provenance.json').write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps(record))


if __name__=='__main__':main()
