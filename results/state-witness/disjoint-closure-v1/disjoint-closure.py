"""Apply the previously frozen finite-action profile to the disjoint corpus."""
import argparse,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('context_analysis',HERE/'context-analysis.py');ca=importlib.util.module_from_spec(spec);spec.loader.exec_module(ca)

def main(spec_source,source,out):
    out.mkdir(parents=True,exist_ok=False);m=json.loads((source/'manifest.json').read_text());profiles={}
    assert hashlib.sha256((HERE/'context-analysis.py').read_bytes()).hexdigest()==m['classifierSha256'],'classifier changed after protocol freeze'
    for c in m['cases']:profiles[c['source']]=ca.finite_profile(k.p.read(spec_source/c['source']))
    (out/'profiles.json').write_text(json.dumps(profiles,indent=2))
    for name in ['disjoint-closure.py','disjoint-closure.mjs','context-analysis.py','observer.cjs']:shutil.copy2(HERE/name,out/name)
    r=subprocess.run(['node',str(HERE/'disjoint-closure.mjs'),str(source.resolve()),str(out.resolve())],capture_output=True,text=True,timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    assert r.returncode==0,r.stderr;print(r.stdout)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('spec',type=Path);p.add_argument('source',type=Path);p.add_argument('out',type=Path)
    v=p.parse_args();main(v.spec,v.source,v.out)
