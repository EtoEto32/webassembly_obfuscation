"""Run a local-only filesystem admission test on existing component binaries."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(source,out):
    expected=json.loads((source/'sha256.json').read_text())
    for relative,digest in expected.items():assert sha(source/relative)==digest
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('fence-file.py','fence-file.cjs','fence-file-plan.md','fence-runtime.cjs'):
        shutil.copy2(HERE/name,out/'sources'/name)
    (out/'component-source.json').write_text(json.dumps({'path':str(source),'hashes':expected},indent=2),encoding='utf8')
    r=subprocess.run(['node',str(HERE/'fence-file.cjs'),str(source),str(out)],capture_output=True,text=True,timeout=60)
    (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    print(r.stdout)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
