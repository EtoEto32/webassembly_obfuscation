import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import prototype as p


SETTINGS={'state2':[0,16],'state3':[0,8,24],'state4':[0,5,13,21]}


def fixture(shifts,seed):
    r=random.Random(seed);n=len(shifts);a=[]
    for i in range(n):
        row=[]
        for j in range(n):
            x=(2*i+3) if i==j else r.getrandbits(16)|1
            row.append((x<<max(0,shifts[j]-shifts[i]))&p.MASK)
        a.append(row)
    b=[r.getrandbits(32)|1 for _ in range(n)]
    c=[((r.getrandbits(20)|1)<<s)&p.MASK for s in shifts]
    return a,b,c


def main(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False);models={};targets=[];transforms=[];recoveries=[]
    for index,(name,shifts) in enumerate(SETTINGS.items()):
        a,b,c=fixture(shifts,20261022+index);models[name]={'a':a,'b':b,'c':c,'shifts':shifts}
        src=root/(name+'-plain.wasm');p.save(p.emit(a,b,c),src)
        assert p.source(src)==(a,b,c)
        variants={'plain':src}
        for mode in ('basis','quotient','perturb'):
            dst=root/(name+'-'+mode+'.wasm');transforms.append({'name':name,**p.transform(src,dst,shifts,mode)})
            variants[mode]=dst
        for mode,raw in variants.items():
            opt=raw.with_stem(raw.stem+'-O3');p.w.tool('wasm-opt',[raw,'-O3','-o',opt])
            for stage,binary in [('raw',raw),('O3',opt)]:
                p.w.tool('wasm-validate',[binary]);targets.append({'name':name,'mode':mode,'stage':stage,'file':binary.name})
                out=binary.with_stem(binary.stem+'-recovered')
                result=p.recover(binary,out,8);recoveries.append({'file':binary.name,**result})
                targets.append({'name':name,'mode':mode+'-recovered','stage':stage,'file':out.name})
        bad=root/(name+'-bad.wasm');bad_result=p.transform(src,bad,shifts,'bad');assert not bad_result['certificate']['transition']
        targets.append({'name':name,'mode':'bad','stage':'raw','negative':True,'file':bad.name})
    manifest={'models':models,'targets':targets,'transforms':transforms,'recoveries':recoveries}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(root)],capture_output=True,text=True,timeout=120)
    (root/'check-stdout.txt').write_text(r.stdout,encoding='utf8');(root/'check-stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    checks=json.loads(r.stdout);(root/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    for file in ('prototype.py','query.cjs','run.py','check.cjs','plan.md'):
        shutil.copyfile(p.HERE/file,root/('source-'+file))
    shutil.copyfile(p.HERE.parent/'connectivity-elimination/prototype.py',root/'source-wat-helper.py')
    pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()}
    (root/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps({'conditions':len(targets),'positive_calls':sum(x['calls'] for x in checks['rows'] if not x['negative']),
                      'recoveries':len(recoveries),'models':[(r['file'],r['model']['order'],r['model']['solver']['pivot_valuations']) for r in recoveries]},indent=2))

if __name__=='__main__':main(sys.argv[1])
