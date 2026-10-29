"""Compare representative specialization with the full affine check on saved binaries."""
import json,shutil,subprocess,sys
from pathlib import Path
import prototype as p
import recover as r
def main(folder,dest):
    folder=Path(folder).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    original=json.loads((folder/'manifest.json').read_text());rows=[];attacks=[]
    shutil.copy2(folder/'cases.json',out/'cases.json')
    for row in original:
        if row['mode']!='sync':continue
        f=out/(Path(row['file']).stem+'-representative.wasm');info=r.recover(folder/row['file'],f,True)
        full=folder/(Path(row['file']).stem+'-recovered.wasm');same=p.q.digest(full)==p.q.digest(f)
        assert same
        attacks.append({'file':row['file'],'identical_to_full_recovery':same,**info});rows.append({**row,'mode':'representative','file':f.name,'bytes':f.stat().st_size})
    p.q.save(out/'manifest.json',rows);p.q.save(out/'attacks.json',attacks)
    proc=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'check.stdout.txt').write_text(proc.stdout,encoding='utf-8');(out/'check.stderr.txt').write_text(proc.stderr,encoding='utf-8');assert proc.returncode==0,proc.stderr
    info=json.loads(proc.stdout);p.q.save(out/'checks.json',info);print(json.dumps({'conditions':len(rows),'calls':info['calls'],'mismatches':info['mismatches']}))
if __name__=='__main__':main(*sys.argv[1:])
