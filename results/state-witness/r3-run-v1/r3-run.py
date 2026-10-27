"""Per-module process deadlines for real recorded workloads, never hide timeouts."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main(audit,original,normalized,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];m=json.loads((audit/'results.json').read_text())
    for c in m['rows']:
        if c['status']!='accepted':continue
        name=Path(c['file']).stem;dest=out/(name+'.json')
        command=['node','--wasm-max-mem-pages=256','--max-old-space-size=512',str(HERE/'r3-run.mjs'),str(audit.resolve()),str(original.resolve()),str(normalized.resolve()),name,str(dest.resolve())]
        try:
            r=subprocess.run(command,capture_output=True,text=True,timeout=45)
            row={'name':name,'status':'compared' if r.returncode==0 else 'process-failure','code':r.returncode,'stdout':r.stdout,'stderr':r.stderr[-8000:]}
        except subprocess.TimeoutExpired as e:row={'name':name,'status':'timeout','seconds':45}
        row['record']=dest.name if dest.exists() else None;rows.append(row);print(json.dumps(row),flush=True)
    for name in ('r3-run.py','r3-run.mjs','observer.cjs'):shutil.copy2(HERE/name,out/name)
    summary={s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})}
    (out/'results.json').write_text(json.dumps({'summary':summary,'rows':rows,'resourceContract':{'maxMemoryPages':256,'maxJsOldSpaceMiB':512,'moduleDeadlineSeconds':45}},indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(summary))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('audit',type=Path);p.add_argument('original',type=Path);p.add_argument('normalized',type=Path);p.add_argument('out',type=Path)
    v=p.parse_args();main(v.audit,v.original,v.normalized,v.out)
