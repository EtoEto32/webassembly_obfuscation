"""Fetch one public npm artifact without running package/install scripts."""
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.tools/masters-security-hash-wasm-4.12.0'
URL='https://registry.npmjs.org/hash-wasm/4.12.0'
EXPECTED_SHA256='1db32a125fb46177932ec8ac438d3cd8214ebdfaccb5d6611b657d88eb586f92'
def fetch(url,limit):
    with urllib.request.urlopen(url,timeout=45) as r:data=r.read(limit+1)
    if len(data)>limit:raise ValueError('download exceeds bound')
    return data
def main():
    if OUT.exists():
        assert hashlib.sha256((OUT/'package.tgz').read_bytes()).hexdigest()==EXPECTED_SHA256
        print((OUT/'provenance.json').read_text());return
    metadata=fetch(URL,1024*1024);meta=json.loads(metadata)
    assert meta['name']=='hash-wasm' and meta['version']=='4.12.0'
    url=meta['dist']['tarball'];assert url=='https://registry.npmjs.org/hash-wasm/-/hash-wasm-4.12.0.tgz'
    data=fetch(url,4*1024*1024);algorithm,encoded=meta['dist']['integrity'].split('-',1)
    assert algorithm=='sha512' and base64.b64encode(hashlib.sha512(data).digest()).decode()==encoded
    assert hashlib.sha256(data).hexdigest()==EXPECTED_SHA256
    members=[];total=0
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
        for m in tar.getmembers():
            if m.isdir():continue
            if not m.isfile():raise ValueError('nonregular archive entry')
            target=(OUT/m.name).resolve()
            if OUT.resolve() not in target.parents or not m.name.startswith('package/'):raise ValueError('archive path')
            total+=m.size
            if total>32*1024*1024:raise ValueError('uncompressed size bound')
            members.append((m,target))
        OUT.mkdir(parents=True,exist_ok=False)
        for m,target in members:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(tar.extractfile(m).read())
    (OUT/'registry.json').write_bytes(metadata)
    (OUT/'package.tgz').write_bytes(data)
    record={'package':'hash-wasm','version':'4.12.0','registry':URL,'tarball':url,
      'sha256':hashlib.sha256(data).hexdigest(),'sha512Integrity':meta['dist']['integrity'],'files':len(members),
      'compressedBytes':len(data),'uncompressedBytes':total,'packageScriptsExecuted':False}
    (OUT/'provenance.json').write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps(record))
if __name__=='__main__':main()
