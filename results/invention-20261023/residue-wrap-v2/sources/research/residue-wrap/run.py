import json
from pathlib import Path
import subprocess
import sys
import prototype as p

P=lambda i:('p',i)
C=lambda i:('c',i)
O=lambda op,a,b:(op,a,b)
CASES={
    'add':O('add',P(0),P(1)),
    'multiply':O('mul',P(0),P(1)),
    'polynomial':O('add',O('mul',O('add',P(0),C(0x9e3779b9)),O('sub',P(1),P(0))),O('mul',P(1),C(17)))
}


def main(dest):
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False);manifest=[];transforms=[];attacks=[]
    for name,e in CASES.items():
        src=out/(name+'-plain-raw.wasm');p.q.compile(p.plain(e),src)
        for mode in ('plain','odd','repair','aligned'):
            raw=out/(name+'-'+mode+'-raw.wasm')
            if mode!='plain':transforms.append(dict(name=name,**p.transform(src,raw,mode)))
            for opt in ('raw','O3'):
                f=out/(name+'-'+mode+'-'+opt+'.wasm')
                if opt=='O3':p.q.w.tool('wasm-opt',[raw,'-O3','-o',f])
                p.q.w.tool('wasm-validate',[f]);manifest.append(dict(name=name,mode=mode,opt=opt,file=f.name,bytes=f.stat().st_size,negative=mode=='odd'))
                if mode=='aligned':
                    dst=out/(f.stem+'-recovered.wasm')
                    try:
                        stats=p.project(f,dst);attacks.append(dict(file=f.name,status='success',**stats))
                        manifest.append(dict(name=name,mode='recovered',opt=opt,file=dst.name,bytes=dst.stat().st_size))
                    except ValueError as ex:attacks.append(dict(file=f.name,status='unsupported',reason=str(ex)))
    p.q.save(out/'cases.json',CASES);p.q.save(out/'manifest.json',manifest);p.q.save(out/'transformations.json',transforms);p.q.save(out/'attacks.json',attacks)
    check=subprocess.run(['node',str(p.HERE/'check.cjs'),str(out)],capture_output=True,text=True,timeout=180)
    (out/'checks.stdout.txt').write_text(check.stdout,encoding='utf-8');(out/'checks.stderr.txt').write_text(check.stderr,encoding='utf-8')
    if check.returncode:raise RuntimeError(check.stderr)
    facts=json.loads(check.stdout);p.q.save(out/'checks.json',facts)
    print(json.dumps(dict(calls=facts['calls'],mismatches=facts['mismatches'],negative_conditions=len(facts['negative']),attacks=attacks)))


if __name__=='__main__':main(sys.argv[1])
