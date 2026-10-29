import json, random, subprocess, sys
from pathlib import Path
import prototype as p

def main(screen,dest):
    screen=json.loads(Path(screen).read_text());out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False)
    # Disclosed discovery selection: first passing gain, otherwise first seed.
    patterns=[[(1,0,1),(2,1,2)],[(0,1,2),(2,0,2)],[(3,0,1),(1,2,1),(2,0,1)]]
    cases={};manifest=[];trans=[];attacks=[]
    for i,ops in enumerate(patterns):
        selected=next((v for v in screen['chosen'] if v['pattern']==i),None)
        seed=selected['seed'] if selected else 213100+i*200;e=list(range(16));random.Random(seed).shuffle(e)
        name='copy'+str(i);cases[name]={'ops':ops,'seed':seed,'encoding':e,'selection':'first gain in 200 discovery seeds' if selected else 'first discovery seed'}
        src=out/(name+'-plain-raw.wasm');p.q.compile(p.plain(ops),src)
        for mode in ('plain','full','linear','color','bad'):
            raw=out/(name+'-'+mode+'-raw.wasm')
            if mode!='plain':trans.append({'name':name,**p.transform(src,raw,e,mode)})
            for opt in ('raw','O3'):
                f=out/(name+'-'+mode+'-'+opt+'.wasm')
                if opt=='O3':p.q.w.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',f])
                manifest.append({'name':name,'mode':mode,'opt':opt,'file':f.name,'bytes':f.stat().st_size,'negative':mode=='bad'})
                if mode in ('full','linear','color'):
                    recovered=out/(f.stem+'-recovered.wasm');attack=p.recover(f,recovered);attacks.append({'file':f.name,**attack})
                    manifest.append({'name':name,'mode':mode+'-recovered','opt':opt,'file':recovered.name,'bytes':recovered.stat().st_size})
    p.q.save(out/'cases.json',cases);p.q.save(out/'manifest.json',manifest);p.q.save(out/'transforms.json',trans);p.q.save(out/'attacks.json',attacks)
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'checks.stdout.txt').write_text(r.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(r.stderr,encoding='utf-8')
    if r.returncode:raise RuntimeError(r.stderr)
    result=json.loads(r.stdout);p.q.save(out/'checks.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('positive','negative')}))
if __name__=='__main__':main(*sys.argv[1:])
