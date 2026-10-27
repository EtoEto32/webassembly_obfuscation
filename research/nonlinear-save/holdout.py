"""Wasm confirmation of the sole gain in the pre-separated holdout screen."""
import json, random, subprocess, sys
from pathlib import Path
import prototype as p

def main(audit,dest):
    audit=json.loads(Path(audit).read_text());out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    patterns=[[(1,0,1),(2,1,2)],[(0,1,2),(2,0,2)],[(3,0,1),(1,2,1),(2,0,1)]]
    cases={};rows=[];trans=[];attacks=[]
    for r in audit['rows']:
        if r['color_bits']>=r['linear_bits']:continue
        name='holdout'+str(r['seed']);ops=patterns[r['pattern']];e=list(range(16));random.Random(r['seed']).shuffle(e)
        cases[name]={'ops':ops,'encoding':e,'seed':r['seed'],'selection':'all gains from previously separated 600-case holdout'}
        src=out/(name+'-plain-raw.wasm');p.q.compile(p.plain(ops),src)
        for mode in ('plain','full','linear','color','bad'):
            raw=out/(name+'-'+mode+'-raw.wasm')
            if mode!='plain':trans.append({'name':name,**p.transform(src,raw,e,mode)})
            for opt in ('raw','O3'):
                f=out/(name+'-'+mode+'-'+opt+'.wasm')
                if opt=='O3':p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',f])
                rows.append({'name':name,'mode':mode,'opt':opt,'file':f.name,'bytes':f.stat().st_size,'negative':mode=='bad'})
                if mode in ('full','linear','color'):
                    recovered=out/(f.stem+'-recovered.wasm');attacks.append({'file':f.name,**p.recover(f,recovered)})
                    rows.append({'name':name,'mode':mode+'-recovered','opt':opt,'file':recovered.name,'bytes':recovered.stat().st_size})
    p.q.save(out/'cases.json',cases);p.q.save(out/'manifest.json',rows);p.q.save(out/'transforms.json',trans);p.q.save(out/'attacks.json',attacks)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr)
    result=json.loads(r.stdout);p.q.save(out/'checks.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('positive','negative')}))
if __name__=='__main__':main(*sys.argv[1:])
