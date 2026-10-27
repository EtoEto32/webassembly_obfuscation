import json, subprocess, sys
from pathlib import Path
import prototype as p
CASES={'quadratic':[3,5,256], 'cubic':[17,3,0,4096], 'mixed4':[12345,7,256,0,16777216]}

def main(dest):
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    rows=[];transforms=[];attacks=[];p.q.save(out/'cases.json',CASES)
    for name,coeff in CASES.items():
        src=out/(name+'-plain-raw.wasm');p.q.compile(p.source(coeff),src)
        for mode in ('plain','full','quotient','bad'):
            raw=out/(name+'-'+mode+'-raw.wasm')
            if mode!='plain':transforms.append({'name':name,**p.transform(src,raw,mode)})
            for opt in ('raw','O3'):
                f=out/(name+'-'+mode+'-'+opt+'.wasm')
                if opt=='O3':p.q.w.tool('wasm-opt',[raw,'-O3','-o',f])
                p.q.w.tool('wasm-validate',[f])
                rows.append({'name':name,'mode':mode,'opt':opt,'file':f.name,'bytes':f.stat().st_size,'negative':mode=='bad'})
                if mode in ('full','quotient'):
                    recovered=out/(f.stem+'-recovered.wasm')
                    try:
                        attack=p.recover(f,recovered);attacks.append({'file':f.name,**attack})
                        rows.append({'name':name,'mode':mode+'-recovered','opt':opt,'file':recovered.name,'bytes':recovered.stat().st_size})
                    except ValueError as e:attacks.append({'file':f.name,'status':'unsupported','reason':str(e)})
        p.q.save(out/'manifest.json',rows);p.q.save(out/'transforms.json',transforms);p.q.save(out/'attacks.json',attacks)
        print(json.dumps({'name':name,'conditions':len(rows),'recovery_candidates':len(attacks)}),flush=True)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr)
    result=json.loads(r.stdout);p.q.save(out/'checks.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('positive','negative')}))
if __name__=='__main__':main(sys.argv[1])
