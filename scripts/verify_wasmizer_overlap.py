"""Independently re-read both distributed copies of WasmBench/Wasmizer matches."""
import csv
import hashlib
import json
import zipfile
from acquire import ROOT


def manifest(name):
    path=ROOT/'data/catalog'/name/'acquisition.jsonl'
    return {r['sha256']:r for line in path.read_text().splitlines()
            if (r:=json.loads(line)).get('sha256')}


def main():
    a=manifest('wasmbench-filtered-archive')
    b=manifest('wasmizer-msr2023-archive')
    meta_path=ROOT/'results/provenance/wasmizer-metadata.jsonl'
    meta={r['sha256']:r for line in meta_path.read_text().splitlines() if (r:=json.loads(line))}
    bench_root=(ROOT/'data/extracted/wasmbench-filtered').resolve()
    records=[]
    with zipfile.ZipFile(ROOT/'data/archives/wasmizer-msr2023-v2.zip') as archive:
        for sha in sorted(a.keys() & b.keys()):
            left=(bench_root/a[sha]['path']).resolve()
            left.relative_to(bench_root)
            row={'sha256':sha,'bytes':a[sha]['bytes'],'wasmbench_path':a[sha]['path'],
                 'wasmizer_path':b[sha]['path'],'wasmbench_archive_sha256':a[sha]['archive_sha256'],
                 'wasmizer_archive_sha256':b[sha]['archive_sha256'],
                 'wasmizer_source_paths_json':json.dumps(meta[sha]['source_paths']),
                 'verification_status':'pending'}
            try:
                h1,h2=hashlib.sha256(),hashlib.sha256()
                equal=True; size1=size2=0
                with left.open('rb') as one,archive.open(b[sha]['path']) as two:
                    while True:
                        c1,c2=one.read(1024*1024),two.read(1024*1024)
                        if not c1 and not c2: break
                        h1.update(c1);h2.update(c2);size1+=len(c1);size2+=len(c2)
                        equal &= c1==c2
                if h1.hexdigest()!=sha or h2.hexdigest()!=sha or not equal:
                    raise ValueError('independent source-byte comparison failed')
                row.update(verification_status='independent_sources_byte_equal',
                           wasmbench_bytes_read=size1,wasmizer_bytes_read=size2)
            except (OSError,ValueError) as exc:
                row.update(verification_status='failed',error=str(exc))
            records.append(row)
    out=ROOT/'results/provenance'
    fields=list(dict.fromkeys(k for r in records for k in r))
    with (out/'wasmizer-wasmbench-overlap.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
    sizes=sorted(r['bytes'] for r in records)
    summary={'shared_sha256':len(records),
             'independent_sources_byte_equal':sum(r['verification_status']=='independent_sources_byte_equal' for r in records),
             'verification_failed':sum(r['verification_status']=='failed' for r in records),
             'bytes_min':min(sizes),'bytes_max':max(sizes),'bytes_total':sum(sizes),
             'scope':'WasmBench author-filtered v1.0 versus Wasmizer Figshare v2 fixed December2022 snapshot',
             'interpretation':'Publicly downloaded versions share these bytes. The exact data used in the paper comparison cannot be reconstructed from this fact alone.'}
    (out/'wasmizer-wasmbench-overlap-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    main()
