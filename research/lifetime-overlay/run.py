import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import fixtures
import prototype as p


def main(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    targets=[];transforms=[];attacks=[];metrics=[]
    for name,make in fixtures.FIXTURES.items():
        src=root/(name+'-plain.wasm');p.save(p.wat.parse(make()),src)
        modes={'plain':src}
        for mode in ('first','conflict'):
            dst=root/(name+'-'+mode+'.wasm')
            transforms.append({'name':name,**p.transform(src,dst,mode)})
            modes[mode]=dst
        for mode,raw in modes.items():
            opt=raw.with_stem(raw.stem+'-O3')
            p.wat.tool('wasm-opt',[raw,'-O3','-o',opt])
            for stage,binary in [('raw',raw),('O3',opt)]:
                p.wat.tool('wasm-validate',[binary])
                targets.append({'name':name,'mode':mode,'stage':stage,'file':binary.name})
                try:
                    m,f,body,types=p.read(binary,extended=True)
                    metrics.append({'file':binary.name,**p.conflict_metric(m)})
                except ValueError as e:
                    metrics.append({'file':binary.name,'unsupported':str(e)})
                out=binary.with_stem(binary.stem+'-recovered')
                try:
                    r=p.recover(binary,out)
                    attacks.append({'file':binary.name,'status':'recovered',**r})
                    targets.append({'name':name,'mode':mode+'-recovered','stage':stage,'file':out.name})
                except ValueError as e:
                    attacks.append({'file':binary.name,'status':'unsupported','reason':str(e)})
        # Semantically wrong, valid allocation: all source cells share address0.
        m,_,_,_=p.read(src)
        def bad(x):
            if x[0] in ('i32.load','i64.load','i32.store','i64.store'):
                a,w,t,j=p.access(x);x[:]=[x[0],'align=1',['i32.const','0'],*x[j+1:]]
            for y in x[1:]:
                if isinstance(y,list):bad(y)
        bad(m);dst=root/(name+'-bad.wasm');p.save(m,dst)
        targets.append({'name':name,'mode':'bad','stage':'raw','negative':True,'file':dst.name})
    manifest={'targets':targets,'transforms':transforms,'attacks':attacks,'metrics':metrics}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(root)],capture_output=True,text=True,timeout=120)
    (root/'check-stdout.txt').write_text(r.stdout,encoding='utf8')
    (root/'check-stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    checks=json.loads(r.stdout);(root/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    for file in ('prototype.py','fixtures.py','run.py','check.cjs','plan.md'):
        shutil.copyfile(p.HERE/file,root/('source-'+file))
    shutil.copyfile(p.HERE.parent/'connectivity-elimination/prototype.py',root/'source-wat-helper.py')
    pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()}
    (root/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps({'positive_conditions':sum(not t.get('negative') for t in targets),
                     'calls':sum(x['calls'] for x in checks['results'] if not x['negative']),
                     'attacks':{s:sum(x['status']==s for x in attacks) for s in ('recovered','unsupported')},
                     'unsupported':[x for x in attacks if x['status']!='recovered'],
                     'transforms':[{k:v for k,v in x.items() if k!='placement'} for x in transforms]},indent=2))

if __name__=='__main__':main(sys.argv[1])
