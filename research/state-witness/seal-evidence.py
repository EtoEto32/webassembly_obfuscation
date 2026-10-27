"""Seal a finished result directory without replacing existing manifests."""
import argparse,hashlib,json,shutil
from pathlib import Path
def main(out,sources):
    if (out/'sha256.json').exists():raise ValueError('Already sealed')
    for src in sources:
        dst=out/src.name
        if dst.exists() and dst.read_bytes()!=src.read_bytes():raise ValueError('Existing source differs: '+str(dst))
        if not dst.exists():shutil.copy2(src,dst)
    data={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'sha256.json').write_text(json.dumps(data,indent=2));print(json.dumps({'files':len(data)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('sources',type=Path,nargs='*');v=p.parse_args();main(v.out,v.sources)
