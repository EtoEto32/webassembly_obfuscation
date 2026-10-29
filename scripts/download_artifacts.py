"""Download public archives as data, with resumable byte ranges and receipts."""
import argparse
import datetime
import hashlib
import json
import time
from pathlib import Path
from acquire import ROOT, get


def download(item):
    folder = ROOT/'data/archives'
    folder.mkdir(parents=True,exist_ok=True)
    dest = folder/item['filename']
    receipt = dest.with_suffix(dest.suffix+'.receipt.json')
    if dest.exists() and receipt.exists():
        old = json.loads(receipt.read_text())
        if old['url'] == item['url'] and dest.stat().st_size == old['bytes']:
            print(item['id'],'already downloaded',flush=True)
            return
    partial = dest.with_suffix(dest.suffix+'.partial')
    for attempt in range(3):
        start = partial.stat().st_size if partial.exists() else 0
        try:
            with get(item['url'], {'Range':f'bytes={start}-'} if start else {}) as response:
                if start and (response.status != 206 or not response.headers.get('Content-Range','').startswith(f'bytes {start}-')):
                    raise ValueError('server did not honor resume range')
                length = response.headers.get('Content-Length')
                expected = start + int(length) if length else item.get('bytes')
                total, last = start, time.monotonic()
                with partial.open('ab' if start else 'wb') as out:
                    while chunk := response.read(1024*1024):
                        out.write(chunk); total += len(chunk)
                        if time.monotonic()-last > 20:
                            print(item['id'],total,'/',expected,flush=True); last=time.monotonic()
                if expected and total != expected:
                    raise ValueError('short download')
                if item.get('bytes') and total != item['bytes']:
                    raise ValueError('size differs from primary metadata')
            break
        except Exception as exc:
            print(item['id'],'attempt',attempt+1,repr(exc),flush=True)
            if attempt == 2:
                raise
    sha, md5 = hashlib.sha256(), hashlib.md5()
    git_blob = hashlib.sha1(b'blob '+str(partial.stat().st_size).encode()+b'\0')
    with partial.open('rb') as source:
        while chunk := source.read(1024*1024):
            sha.update(chunk); md5.update(chunk); git_blob.update(chunk)
    if item.get('md5') and item['md5'] != md5.hexdigest():
        raise ValueError('upstream MD5 mismatch')
    if item.get('git_blob_sha1') and item['git_blob_sha1'] != git_blob.hexdigest():
        raise ValueError('pinned Git blob mismatch')
    if item.get('file_magic_hex'):
        magic = bytes.fromhex(item['file_magic_hex'])
        with partial.open('rb') as source:
            if source.read(len(magic)) != magic:
                raise ValueError('download is not the expected file type')
    partial.replace(dest)
    result = {**item,'bytes':dest.stat().st_size,'sha256':sha.hexdigest(),'md5':md5.hexdigest(),
              'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    receipt.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('ids',nargs='+'); args=ap.parse_args()
    entries=json.loads((ROOT/'experiments/archive-registry.json').read_text())
    for item in entries:
        if item['id'] in args.ids:
            download(item)
