import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def main(out):
    manifests=[ROOT/'results'/p/'hashes.json' for p in (
        'failure-revocation/probe-v4','failure-revocation/performance-v1',
        'gc-field-policy/probe-v3','gc-field-policy/boundary-v1',
        'gc-field-policy/workload-v2','gc-field-policy/workload-contract-v2','gc-field-policy/link-v3',
        'gc-field-policy/descriptor-interpreter-v1')]
    rows=[];errors=[]
    for manifest in manifests:
        entries=json.loads(manifest.read_text());count=0
        for rel,digest in entries.items():
            file=manifest.parent/rel
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=digest:errors.append(str(file))
            count+=1
        rows.append(dict(manifest=str(manifest.relative_to(ROOT)),files=count))
    # Rebuild each workload's binary from the generator, including the stronger
    # cached-view baseline, without modifying any recorded result.
    from workload import producer,consumer,MODES,w
    rebuilt=[]
    for mode in MODES:
        for suffix,wat in (('lib',producer(mode)),('client',consumer(mode))):
            file=ROOT/f'results/gc-field-policy/workload-v2/{mode}-{suffix}.wasm'
            same=bytes(w.wat2wasm(wat))==file.read_bytes();rebuilt.append(dict(file=str(file.relative_to(ROOT)),identical=same))
            if not same:errors.append(str(file))
    result=dict(manifests=rows,totalFiles=sum(x['files'] for x in rows),regenerated=rebuilt,errors=errors)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2));assert not errors,result
    print(json.dumps(dict(manifests=len(rows),files=result['totalFiles'],regenerated=len(rebuilt),errors=len(errors))))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
