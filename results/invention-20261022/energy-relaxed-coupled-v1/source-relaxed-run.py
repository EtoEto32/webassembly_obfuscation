# -*- coding: utf-8 -*-
import hashlib
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import relaxed as r
import run as old


def fixtures():
    fs=old.fixtures()
    for name,(I,gs) in list(fs.items()):
        fs['correlated-'+name]=(3,[[op,*[[kind,index%3 if kind=='input' else index] for kind,index in (a,b)]] for op,a,b in gs])
    # Follow-up after the six initial fixtures reproduced dominance weights:
    # (x2 & x3) <= (x2 | x3) on valid states, but not on arbitrary internal states.
    x=lambda i:['input',i]
    g=lambda i:['gate',i]
    fs['ordered-guards']=(4,[['xor',x(0),x(1)],['and',x(2),x(3)],['or',x(2),x(3)],
                            ['and',g(0),g(1)],['or',g(0),g(2)],['xor',g(3),g(4)]])
    return fs


def main(dst,only=None):
    root=Path(dst);root.mkdir(parents=True,exist_ok=False)
    models={};targets=[];transforms=[];attacks=[];probes=[];naive=[];flat=[]
    for name,(I,gs) in fixtures().items():
        if only and name!=only:continue
        print('begin '+name,flush=True);models[name]={'inputs':I,'gates':gs};src=root/(name+'-plain.wasm');r.p.save(r.p.plain(I,gs),src)
        variants={'plain':src}
        for mode in ('dag','synth'):
            out=root/(name+'-'+mode+'.wasm');t=r.transform(src,out,mode);variants[mode]=out
            smt=t['synthesis'].pop('smt2',None)
            if smt:(root/(name+'-no-false-minimum.smt2')).write_text(smt,encoding='utf8')
            transforms.append({'name':name,'mode':mode,**t})
            (root/(name+'-'+mode+'-transform.json')).write_text(json.dumps(t,indent=2),encoding='utf8')
            probe=root/(name+'-'+mode+'-probe.wasm');r.p.save(r.render(t['record'],probe=True),probe)
            probes.append({'name':name,'mode':mode,'file':probe.name,'n':len(gs)})
            print(json.dumps({'name':name,'mode':mode,'weights':t['weights'],'rounds':len(t['synthesis'].get('trace',[])),'strict_deviation':t['deviation']['strict']['status']}),flush=True)
        for mode,raw in variants.items():
            opt=raw.with_stem(raw.stem+'-O3');r.p.w.tool('wasm-opt',[raw,'-O3','-o',opt])
            for stage,binary in [('raw',raw),('O3',opt)]:
                r.p.w.tool('wasm-validate',[binary]);targets.append({'name':name,'mode':mode,'stage':stage,'file':binary.name,'negative':False})
                if mode=='plain':continue
                out=binary.with_stem(binary.stem+'-recovered');a=r.recover(binary,out);attacks.append({'name':name,'mode':mode,'stage':stage,'file':binary.name,**a})
                targets.append({'name':name,'mode':mode+'-recovered','stage':stage,'file':out.name,'negative':False})
                # Old local-rule attack is run on the actual public aggregate.
                public=r.p.rawdata(r.p.w.parse(r.p.w.tool('wasm2wat',[binary,'--fold-exprs'])))
                start=time.perf_counter()
                try:m=r.p.recover_model(public);item={'status':'recovered','model':m}
                except ValueError as e:item={'status':'unsupported','reason':str(e)}
                naive.append({'file':binary.name,**item,'milliseconds':(time.perf_counter()-start)*1000})
        f=r.verify(I,gs,[1]*len(gs));f.pop('smt2');flat.append({'name':name,**f})
    manifest={'models':models,'targets':targets,'transforms':transforms,'attacks':attacks,'probes':probes,'old_attack':naive,'flat_controls':flat,'z3':r.z3.get_version_string()}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    for script,label in [('check.cjs','checks'),('relaxed-probe.cjs','all-initial-checks')]:
        check=subprocess.run(['node',str(r.p.HERE/script),str(root)],capture_output=True,text=True,timeout=120)
        (root/(label+'-stderr.txt')).write_text(check.stderr,encoding='utf8')
        (root/(label+'.json')).write_text(check.stdout,encoding='utf8')
        if check.returncode:raise RuntimeError(check.stderr)
    for file in ('relaxed.py','relaxed-run.py','relaxed-probe.cjs','relaxed-plan.md','prototype.py','run.py','check.cjs'):
        shutil.copyfile(r.p.HERE/file,root/('source-'+file))
    shutil.copyfile(r.p.HERE.parent/'connectivity-elimination/prototype.py',root/'source-wat-helper.py')
    pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()}
    (root/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps({'conditions':len(targets),'recoveries':len(attacks),'old_attack_unsupported':sum(x['status']=='unsupported' for x in naive),'pins':len(pins)}),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');ap.add_argument('--only',choices=list(fixtures()));a=ap.parse_args();main(a.output,a.only)
