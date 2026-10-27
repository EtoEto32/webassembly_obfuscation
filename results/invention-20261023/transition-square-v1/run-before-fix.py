import json,subprocess,sys
from pathlib import Path
import prototype as p
B=lambda i,neg=0:('bit',i,neg)
O=lambda op,a,b:(op,a,b)
def fixture(bits):
    groups=[O('and',B(i,i%3==2),B(i+1,(i+1)%3==2)) for i in range(0,bits,2)]
    while len(groups)>1:
        groups=[O('or' if len(groups)%2==0 else 'and',groups[i],groups[i+1]) if i+1<len(groups) else groups[i] for i in range(0,len(groups),2)]
    return groups[0]
def main(dest):
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False);manifest=[];trans=[];attacks=[]
    cases={f'bits{n}':{'bits':n,'tree':fixture(n)} for n in (4,8,12)}
    p.q.save(out/'cases.json',cases)
    for name,case in cases.items():
        src=out/(name+'-plain-raw.wasm');p.q.compile(p.plain(case['tree']),src)
        for opt in ('raw','O3'):
            f=out/(name+'-plain-'+opt+'.wasm')
            if opt=='O3':p.q.w.tool('wasm-opt',[src,'-O3','-o',f])
            manifest.append({'name':name,'mode':'plain','opt':opt,'seed':0,'file':f.name,'bytes':f.stat().st_size})
        for mode in ('base','square','bad-square'):
            for seed in (213071,213072):
                raw=out/(f'{name}-{mode}-{seed}-raw.wasm');stats=p.transform(src,raw,mode,seed)
                trans.append({'name':name,'mode':mode,'seed':seed,**stats})
                for opt in ('raw','O3'):
                    f=out/(f'{name}-{mode}-{seed}-{opt}.wasm')
                    if opt=='O3':p.q.w.tool('wasm-opt',[raw,'-O3','-o',f])
                    p.q.w.tool('wasm-validate',[f]);manifest.append({'name':name,'mode':mode,'opt':opt,'seed':seed,'file':f.name,'bytes':f.stat().st_size,'nodes':stats['nodes'],'negative':mode=='bad-square'})
                    if mode!='bad-square':
                        recovered=out/(f.stem+'-recovered.wasm')
                        try:
                            attack=p.recover(f,recovered);attacks.append({'file':f.name,'status':'success',**attack})
                            manifest.append({'name':name,'mode':mode+'-recovered','opt':opt,'seed':seed,'file':recovered.name,'bytes':recovered.stat().st_size})
                        except ValueError as e:attacks.append({'file':f.name,'status':'unsupported','reason':str(e)})
        p.q.save(out/'manifest.json',manifest);p.q.save(out/'transforms.json',trans);p.q.save(out/'attacks.json',attacks)
        print(json.dumps({'name':name,'attacks':attacks[-8:]}),flush=True)
    check=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=240)
    (out/'checks.stdout.txt').write_text(check.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(check.stderr,encoding='utf-8')
    if check.returncode:raise RuntimeError(check.stderr)
    result=json.loads(check.stdout);p.q.save(out/'checks.json',result)
    print(json.dumps({'positive_conditions':len(result['positive']),'calls':result['calls'],'mismatches':result['mismatches'],'negative_conditions':len(result['negative']),'recovered':sum(x['status']=='success' for x in attacks)}))
if __name__=='__main__':main(sys.argv[1])
