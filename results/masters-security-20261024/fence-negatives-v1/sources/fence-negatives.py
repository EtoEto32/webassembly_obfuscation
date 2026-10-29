"""Local demonstrations of three explicit host-contract violations."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import fence

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(source,out):
    hashes=json.loads((source/'sha256.json').read_text())
    for relative,digest in hashes.items():assert sha(source/relative)==digest
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('fence-negatives.py','fence-negatives.cjs','fence-negatives-plan.md','fence-runtime.cjs','fence.py','fence.wit','fence-policy.json'):
        shutil.copy2(HERE/name,out/'sources'/name)
    model=fence.Reader((HERE/'fence.wit').read_text()).parse();policy=json.loads((HERE/'fence-policy.json').read_text())
    policy['permissions']['value/@copy/destination']='read'
    (out/'wrong-policy.json').write_text(json.dumps(policy,indent=2),encoding='utf8')
    # Well-typed and path-complete does not mean semantically authorized.
    (out/'wrong-project.cjs').write_text(fence.generate(model,policy,'jco-host'),encoding='utf8')
    (out/'source.json').write_text(json.dumps({'path':str(source),'hashes':hashes},indent=2),encoding='utf8')
    try:
        r=subprocess.run(['node',str(HERE/'fence-negatives.cjs'),str(source),str(out)],capture_output=True,text=True,timeout=30)
        (out/'stdout.txt').write_text(r.stdout,encoding='utf8');(out/'stderr.txt').write_text(r.stderr,encoding='utf8')
        assert r.returncode==0,r.stderr;print(r.stdout)
    finally:(out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='sha256.json'},indent=2),encoding='utf8')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
