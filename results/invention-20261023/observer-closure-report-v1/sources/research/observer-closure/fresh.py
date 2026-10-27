"""Adaptive follow-up: remove reset/peek from both compared API profiles."""
import json, subprocess, sys
from pathlib import Path
import prototype as p

def main(folder,dest):
    folder=Path(folder).resolve();out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    cases=json.loads((folder/'cases.json').read_text());p.q.save(out/'cases.json',cases)
    rows=[];attacks=[]
    for row in json.loads((folder/'manifest.json').read_text()):
        if row.get('negative') or row['mode'] not in ('plain','full','quotient'):continue
        m=p.q.read(folder/row['file']);m=[m[0],*[e for e in m[1:] if not (e[0]=='export' and e[1] in ('"reset"','"peek"'))]]
        f=out/row['file'];p.q.compile(p.q.w.emit(m),f)
        rows.append({**row,'bytes':f.stat().st_size})
        if row['mode'] in ('full','quotient'):
            recovered=out/(f.stem+'-recovered.wasm');a=p.recover(f,recovered,fresh=True);attacks.append({'file':f.name,**a})
            rows.append({**row,'mode':row['mode']+'-recovered','file':recovered.name,'bytes':recovered.stat().st_size})
            coeff=a['coefficients_mod_2_31'];original=cases[row['name']];degree=max(len(coeff),len(original))-1
            vals=[(p.d.evaluate(coeff,s)-p.d.evaluate(original,s))% (1<<31) for s in range(degree+1)];diff=[]
            while vals:diff.append(vals[0]);vals=[(vals[i+1]-vals[i])% (1<<31) for i in range(len(vals)-1)]
            assert not any(diff);a['all_integer_polynomial_certificate']=diff
    p.q.save(out/'manifest.json',rows);p.q.save(out/'attacks.json',attacks)
    r=subprocess.run(['node',str(p.HERE/'fresh_check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr)
    result=json.loads(r.stdout);p.q.save(out/'checks.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':main(*sys.argv[1:])
