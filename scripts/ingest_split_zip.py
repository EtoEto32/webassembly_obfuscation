"""Ingest all Wasm members from byte-concatenated public release assets."""
import argparse
import bisect
import io
import json
import zipfile
from acquire import ROOT
from ingest_archives import OBJECTS, walk_zip


class LocalParts(io.RawIOBase):
    def __init__(self, paths):
        self.files = [p.open('rb') for p in paths]
        self.starts = [0]
        for p in paths:
            self.starts.append(self.starts[-1]+p.stat().st_size)
        self.pos = 0

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos+offset if whence == 1 else self.starts[-1]+offset
        if self.pos < 0:
            raise ValueError('negative seek')
        return self.pos

    def read(self, size=-1):
        if size < 0: size = self.starts[-1]-self.pos
        size = min(size, self.starts[-1]-self.pos)
        chunks = []
        while size > 0:
            i = bisect.bisect_right(self.starts,self.pos)-1
            offset = self.pos-self.starts[i]
            count = min(size,self.starts[i+1]-self.pos)
            self.files[i].seek(offset)
            chunk = self.files[i].read(count)
            if len(chunk) != count:
                raise OSError('short archive-part read')
            chunks.append(chunk); self.pos += count; size -= count
        return b''.join(chunks)

    def close(self):
        for f in self.files: f.close()
        super().close()


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('variant',choices=['binaries','binaries-opt']); args=ap.parse_args()
    registry=json.loads((ROOT/'experiments/archive-registry.json').read_text())
    items=sorted([r for r in registry if r['dataset']=='wasm-obf' and r.get('asset_name','').startswith(args.variant+'.zip.')],key=lambda r:r['asset_name'])
    paths=[ROOT/'data/archives'/r['filename'] for r in items]
    receipts=[json.loads(p.with_suffix(p.suffix+'.receipt.json').read_text()) for p in paths]
    for p,r in zip(paths,receipts):
        if p.stat().st_size != r['bytes']: raise ValueError('archive-part size mismatch')
    ident='wasm-obf-release-'+args.variant
    output=ROOT/'data/catalog'/ident; output.mkdir(parents=True,exist_ok=True); OBJECTS.mkdir(parents=True,exist_ok=True)
    item={'id':ident,'dataset':'wasm-obf','url':'https://github.com/HakonHarnes/wasm-obf/releases/tag/v1.0',
          'sha256':None}
    rows,inventory,failures=[],[],[]
    with LocalParts(paths) as stream, zipfile.ZipFile(stream) as z:
        walk_zip(z,item,rows,inventory,failures)
    for row in rows:
        row['archive_part_sha256']=[r['sha256'] for r in receipts]
        row['release_variant']=args.variant
    (output/'inventory.json').write_text(json.dumps(inventory),encoding='utf-8')
    (output/'archive-parts.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
    (output/'acquisition.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    summary={'dataset':'wasm-obf','artifact':ident,'archive_members':len(inventory),
             'candidate_wasm_members':len(rows),'unique_downloaded_sha256':len({r['sha256'] for r in rows if r['sha256']}),
             'stored_verified_paths':sum(r['acquisition_status']=='stored_verified' for r in rows),
             'failures':failures,'scope':'all regular members inspected; standalone Wasm and nested ZIP/APK/JAR; no arbitrary JS execution'}
    (output/'acquisition-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__=='__main__': main()
