"""Run every generated variant with its own deadline and durable partial logs."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for name in ('r3-weave-run.py','r3-weave-run.mjs','directory-observer.cjs','observer.cjs'):shutil.copy2(HERE/name,out/name)
    shutil.copy2(source/'weave.mjs',out/'weave.mjs')
    for r in json.loads((source/'results.json').read_text())['rows']:
        if r['status']!='valid':continue
        for mode in ('continuous','restore'):
            dest=out/(r['name']+'-'+r['kind']+'-'+mode+'.json')
            cmd=['node','--wasm-max-mem-pages=512','--max-old-space-size=512',str(out/'r3-weave-run.mjs'),str(source.resolve()),r['name'],r['kind'],mode,str(dest.resolve())]
            row={'name':r['name'],'kind':r['kind'],'mode':mode,'record':dest.name}
            try:
                p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=60)
                row.update({'code':p.returncode,'stderr':p.stderr[-6000:]})
                row['status']=json.loads(dest.read_text()).get('status','incomplete') if p.returncode==0 else 'process-failure'
            except subprocess.TimeoutExpired:row.update({'status':'timeout','seconds':60})
            rows.append(row);print(json.dumps(row),flush=True)
            (out/'partial.json').write_text(json.dumps(rows,indent=2))
    result={'rows':rows,'sourceManifestSha256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
      'resourceContract':{'physicalPages':512,'maxJsOldSpaceMiB':512,'perConditionSeconds':60},
      'summary':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})}}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2));print(json.dumps(result['summary']))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.out)
