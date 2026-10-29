import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]


def main(report,out):
    report=Path(report).resolve();out=Path(out).resolve()
    if out.exists():raise FileExistsError(out)
    records=json.loads((report/'provenance.json').read_text(encoding='utf-8'))['files']
    for row in records:
        f=Path(row['path']);data=f.read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise AssertionError(f)
    source=[]
    for f in Path(__file__).resolve().parent.glob('*.py'):
        compile(f.read_text(encoding='utf-8'),str(f),'exec');source.append(str(f.relative_to(ROOT)))
    out.write_text(json.dumps(dict(hash_pins=len(records),hash_mismatches=0,python_syntax=source),indent=2),encoding='utf-8')
    print(len(records),'hashes verified')


if __name__=='__main__':main(*sys.argv[1:])
