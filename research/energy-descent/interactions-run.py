# -*- coding: utf-8 -*-
import hashlib
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import interactions as p

def main(dst,robust=False):
    root=Path(dst);root.mkdir(parents=True,exist_ok=False);models={};targets=[];transforms=[];attacks=[];probes=[];ablations=[]
    for name,(I,gs) in p.screen.fixtures().items():
        models[name]={'inputs':I,'gates':gs};src=root/(name+'-plain.wasm');p.r.p.save(p.r.p.plain(I,gs),src);variants={'plain':src}
        dag=root/(name+'-dag.wasm');base=p.r.transform(src,dag,'dag');transforms.append({'name':name,'mode':'dag',**base});variants['dag']=dag
        out=root/(name+'-interaction.wasm');t=p.transform(src,out,robust);variants['interaction']=out
        (root/(name+'-synthesis.smt2')).write_text(t['synthesis'].pop('smt2'),encoding='utf8')
        transforms.append({'name':name,'mode':'interaction',**t})
        drop=p.build(I,gs,t['synthesis']['weights'],[]);c=p.public_certificate(drop)
        ablations.append({'name':name,'record':drop,'public_certificate':c})
        # Full all-input/all-initial-state probes for the two positive modes.
        for mode,record in [('dag',base['record']),('interaction',t['record'])]:
            probe=root/(name+'-'+mode+'-probe.wasm');p.r.p.save(p.r.render(record,probe=True),probe);probes.append({'name':name,'mode':mode,'file':probe.name,'n':len(gs)})
        for mode,raw in variants.items():
            opt=raw.with_stem(raw.stem+'-O3');p.r.p.w.tool('wasm-opt',[raw,'-O3','-o',opt])
            for stage,binary in [('raw',raw),('O3',opt)]:
                targets.append({'name':name,'mode':mode,'stage':stage,'file':binary.name,'negative':False})
                if mode=='plain':continue
                recovered=binary.with_stem(binary.stem+'-recovered');a=p.recover(binary,recovered)
                attacks.append({'name':name,'mode':mode,'stage':stage,'file':binary.name,**a});targets.append({'name':name,'mode':mode+'-recovered','stage':stage,'file':recovered.name,'negative':False})
        print(json.dumps({'name':name,'weights':t['synthesis']['weights'],'interactions':t['synthesis']['interactions'],'recovered':4,'terms':len(t['record']['terms'])}),flush=True)
    m={'models':models,'targets':targets,'transforms':transforms,'attacks':attacks,'probes':probes,'ablations':ablations}
    (root/'manifest.json').write_text(json.dumps(m,indent=2),encoding='utf8')
    for script,label in [('check.cjs','checks'),('relaxed-probe.cjs','all-initial-checks')]:
        proc=subprocess.run(['node',str(p.r.p.HERE/script),str(root)],capture_output=True,text=True,timeout=120)
        (root/(label+'.json')).write_text(proc.stdout,encoding='utf8');(root/(label+'-stderr.txt')).write_text(proc.stderr,encoding='utf8')
        if proc.returncode:raise RuntimeError(proc.stderr)
    # Valid family bytes with false minima must now be rejected without source.
    rejected=[]
    for a in ablations:
        if a['public_certificate']['accepted']:continue
        binary=root/(a['name']+'-drop.wasm');p.r.p.save(p.r.render(a['record']),binary)
        try:p.recover(binary,root/(a['name']+'-drop-recovered.wasm'));raise AssertionError('Uncertified energy accepted')
        except ValueError as e:assert 'Public energy certificate rejected' in str(e);rejected.append({'file':binary.name,'reason':str(e)})
    (root/'rejections.json').write_text(json.dumps(rejected,indent=2),encoding='utf8')
    for name in ('interactions.py','interactions-screen.py','interactions-run.py','relaxed.py','prototype.py','check.cjs','relaxed-probe.cjs'):
        shutil.copyfile(p.r.p.HERE/name,root/('source-'+name))
    shutil.copyfile(p.r.p.HERE.parent/'connectivity-elimination/prototype.py',root/'source-wat-helper.py')
    (root/'pins.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'targets':len(targets),'recoveries':len(attacks),'rejected_ablations':len(rejected)}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');ap.add_argument('--robust-selectors',action='store_true');a=ap.parse_args();main(a.output,a.robust_selectors)
