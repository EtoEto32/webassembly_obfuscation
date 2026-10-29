"""Separate purposive sample of a threaded application, never pooled as prevalence."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];EXE=ROOT/'.tools/state-witness-census-target/release/wasm-lifetime-census.exe'


def main(source,out):
    source=source.resolve();out.mkdir(parents=True,exist_ok=False);provenance=json.loads((source/'provenance.json').read_text());rows=[]
    for package in provenance['rows']:
        item=next(r for r in package['files'] if r['file'].endswith('.wasm'));file=source/item['file'];assert hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256']
        run=subprocess.run([str(EXE),str(file)],capture_output=True,text=True,encoding='utf8',timeout=45);assert run.returncode==0,run.stderr;scan=json.loads(run.stdout)
        row={'package':package['package'],'source':str(file.relative_to(ROOT)),'sha256':item['sha256'],'scan':scan};rows.append(row)
        print(json.dumps({'package':package['package'],'status':scan['status'],'counts':scan.get('counts'),'start':scan.get('start'),'passive':sum(s['passive'] for s in scan.get('data',[])),'functionsWithLifetimeInstructions':[f['functionIndex'] for f in scan.get('functions',[])]}),flush=True)
    (out/'results.json').write_text(json.dumps({'rows':rows,'scope':'Purposive static sample, not dynamic reproduction or K-profile acceptance. Kept separate from the older corpora.','executableSha256':hashlib.sha256(EXE.read_bytes()).hexdigest()},indent=2))
    shutil.copy2(source/'provenance.json',out/'provenance.json')
    for name in ('modern-census.py','modern-corpus-plan.md','fetch-modern-corpus.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
