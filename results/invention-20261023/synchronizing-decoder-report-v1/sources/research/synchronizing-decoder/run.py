import json, subprocess, sys
from pathlib import Path
import prototype as p
import recover as r
def main(dest):
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False);cases={};rows=[];trans=[];attacks=[]
    for rounds in (1,3,8):
        text,co=p.source(rounds,231100+rounds);name='round'+str(rounds);cases[name]={'rounds':rounds,'coefficients':co}
        plain=out/(name+'-plain-raw.wasm');p.q.compile(text,plain)
        opt=out/(name+'-plain-O3.wasm');p.q.w.tool('wasm-opt',[plain,'-O3','-o',opt])
        for label,f in [('raw',plain),('O3',opt)]:rows.append({'name':name,'mode':'plain','n':0,'opt':label,'file':f.name,'bytes':f.stat().st_size})
        for n in (4,8):
            for mode in ('fixed','sync','bad'):
                raw=out/('%s-n%d-%s-raw.wasm'%(name,n,mode));info=p.transform(plain,raw,n,231200+rounds*10+n,mode);trans.append({'name':name,**info})
                for label in ('raw','O3'):
                    f=out/('%s-n%d-%s-%s.wasm'%(name,n,mode,label))
                    if label=='O3':p.q.w.tool('wasm-opt',[raw,'-O3','-o',f])
                    rows.append({'name':name,'mode':mode,'n':n,'opt':label,'file':f.name,'bytes':f.stat().st_size,'negative':mode=='bad'})
                    if mode!='bad':
                        recovered=out/(f.stem+'-recovered.wasm');info=r.recover(f,recovered);attacks.append({'file':f.name,**info})
                        rows.append({'name':name,'mode':mode+'-recovered','n':n,'opt':label,'file':recovered.name,'bytes':recovered.stat().st_size})
    p.q.save(out/'cases.json',cases);p.q.save(out/'manifest.json',rows);p.q.save(out/'transforms.json',trans);p.q.save(out/'attacks.json',attacks)
    result=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'check.stdout.txt').write_text(result.stdout,encoding='utf-8');(out/'check.stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(result.stderr)
    checks=json.loads(result.stdout);p.q.save(out/'checks.json',checks);print(json.dumps({k:v for k,v in checks.items() if k not in ('positive','negative')}))
if __name__=='__main__':main(sys.argv[1])
