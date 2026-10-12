"""Inventory the author's uncompressed TAR through verified HTTP byte ranges.

Read every regular-member header and magic, retrieve complete Wasm members,
and retain all source offsets. Never extract archive paths onto the filesystem.
"""
import argparse
import collections
import datetime
import hashlib
import io
import json
import tarfile
import time
from acquire import ROOT,get

URL='https://download.vusec.net/dataset/cryptominers_dataset.tar'


class RemoteTar(io.RawIOBase):
    def __init__(self,meta,block_size=262144):
        self.size=int(meta['headers']['Content-Length']);self.etag=meta['headers']['ETag']
        self.pos=0;self.block_size=block_size;self.requests=0;self.downloaded=0
        self.cache=ROOT/'data/remote-tar-cache'/hashlib.sha256((URL+'|'+self.etag).encode()).hexdigest()[:24]
        self.cache.mkdir(parents=True,exist_ok=True)

    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        dest=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        if dest<0:raise ValueError('negative seek')
        self.pos=dest;return dest

    def read(self,n=-1):
        if n<0:raise ValueError('unbounded remote read refused')
        remaining=min(n,max(0,self.size-self.pos));parts=[]
        while remaining:
            start=self.pos//self.block_size*self.block_size
            end=min(start+self.block_size,self.size)-1
            path=self.cache/(str(start)+'.bin');receipt=path.with_suffix('.json')
            if path.exists() and receipt.exists():
                raw=path.read_bytes();proof=json.loads(receipt.read_text(encoding='utf-8'))
                if len(raw)!=end-start+1 or hashlib.sha256(raw).hexdigest()!=proof['sha256']:
                    raise ValueError('cached range corrupted')
            else:
                for attempt in range(3):
                    try:
                        with get(URL,{'Range':f'bytes={start}-{end}','If-Match':self.etag}) as response:
                            if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{self.size}':
                                raise ValueError('server did not return requested range; full download refused')
                            if response.headers.get('ETag')!=self.etag:raise ValueError('upstream identity changed')
                            raw=response.read(end-start+2)
                            if len(raw)!=end-start+1:raise ValueError('range length mismatch')
                        break
                    except Exception:
                        if attempt==2:raise
                path.write_bytes(raw)
                receipt.write_text(json.dumps({'start':start,'end':end,'url':URL,'etag':self.etag,
                                              'sha256':hashlib.sha256(raw).hexdigest()}),encoding='utf-8')
                self.requests+=1;self.downloaded+=len(raw)
            offset=self.pos-start;take=min(remaining,len(raw)-offset)
            parts.append(raw[offset:offset+take]);self.pos+=take;remaining-=take
        return b''.join(parts)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preview',type=int);args=ap.parse_args()
    meta=json.loads((ROOT/'results/catalog/minesweeper-archive-head.json').read_text(encoding='utf-8'))
    remote=RemoteTar(meta);base=ROOT/'data/catalog/minesweeper-crawled-archive';base.mkdir(parents=True,exist_ok=True)
    inventory=base/('preview.jsonl' if args.preview else 'inventory.jsonl.partial')
    acquisition=base/('preview-acquisition.jsonl' if args.preview else 'acquisition.jsonl.partial')
    checkpoint=base/('preview-summary.json' if args.preview else 'scan-progress.json')
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();count=0;regular=0;rows=[];prefixes=collections.Counter();archives=[];last=time.monotonic()
    with inventory.open('w',encoding='utf-8') as inv,acquisition.open('w',encoding='utf-8') as acq,tarfile.open(fileobj=remote,mode='r:') as archive:
        for member in archive:
            count+=1
            item={'path':member.name,'bytes':member.size,'type':member.type.decode('ascii',errors='replace'),
                  'header_offset':member.offset,'data_offset':member.offset_data,'archive_mtime':member.mtime,
                  'mtime_semantics':'archive member modification time; not a confirmed observation date'}
            if member.isfile():
                regular+=1;source=archive.extractfile(member);prefix=source.read(8)
                is_wasm=prefix[:4]==b'\0asm';item['magic_hex']=prefix.hex();item['wasm_magic']=is_wasm
                prefixes[member.name.split('/')[0]]+=1
                if prefix.startswith((b'PK\x03\x04',b'\x1f\x8b',b'7z\xbc\xaf\x27\x1c')):
                    archives.append({'path':member.name,'bytes':member.size,'magic_hex':prefix.hex()})
                if is_wasm or member.name.lower().endswith('.wasm'):
                    raw=prefix+source.read();sha=hashlib.sha256(raw).hexdigest()
                    path=ROOT/'data/objects'/(sha+'.bin');status='stored_verified';error=None
                    try:
                        if not path.exists():path.write_bytes(raw)
                        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('object mismatch')
                    except OSError as exc:status='local_io_failed';error=str(exc)
                    row={'dataset':'minesweeper','artifact':'minesweeper-crawled','path':member.name,
                         'bytes':len(raw),'sha256':sha,'object':path.relative_to(ROOT).as_posix(),
                         'wasm_magic':is_wasm,'acquisition_status':status,'acquisition_error':error,
                         'archive_url':URL,'archive_etag':remote.etag,'archive_bytes':remote.size,
                         'data_offset':member.offset_data,'archive_member_mtime':member.mtime,
                         'hash_evidence':'computed from complete member bytes read via verified HTTP ranges'}
                    rows.append(row);acq.write(json.dumps(row)+'\n')
            inv.write(json.dumps(item)+'\n')
            if args.preview and count>=args.preview:break
            if time.monotonic()-last>20:
                inv.flush();acq.flush()
                progress={'members':count,'regular_members':regular,'wasm_occurrences':len(rows),
                          'offset':remote.tell(),'total_archive_bytes':remote.size,'requests_this_run':remote.requests,
                          'downloaded_bytes_this_run':remote.downloaded,'status':'incomplete_running'}
                checkpoint.write_text(json.dumps(progress,indent=2),encoding='utf-8');print(json.dumps(progress),flush=True);last=time.monotonic()
    summary={'dataset':'minesweeper','artifact':'minesweeper-crawled','archive_url':URL,'archive_bytes':remote.size,'archive_etag':remote.etag,
             'started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'members':count,'regular_members':regular,'wasm_paths':len(rows),'unique_sha256':len({r['sha256'] for r in rows}),
             'local_io_failed_paths':sum(r['acquisition_status']!='stored_verified' for r in rows),
             'requests_this_run':remote.requests,'downloaded_bytes_this_run':remote.downloaded,
             'archive_like_members':archives,'top_directory_counts':dict(prefixes),
             'scope':'preview_incomplete' if args.preview else 'all outer TAR members indexed; all regular member magic checked; nested archives listed separately',
             'whole_archive_sha256':None,'integrity_scope':'Per-range SHA256 plus stable ETag/size; SHA256 for every retrieved full Wasm member. No claim of full-archive checksum validation.'}
    if not args.preview:
        inventory.replace(base/'inventory.jsonl');acquisition.replace(base/'acquisition.jsonl')
        (base/'acquisition-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    checkpoint.write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
