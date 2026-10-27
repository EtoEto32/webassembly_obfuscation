import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import prototype as p

def inp(i):return ['input',i]
def gate(i):return ['gate',i]
def fixtures():
    chain=[['xor',inp(0),inp(1)]]
    for i in range(1,8):chain.append([['and','or','xor'][i%3],gate(i-1),inp(i+1)])
    diamond=[['and',inp(0),inp(1)],['xor',inp(2),inp(3)],['or',inp(4),inp(5)],
             ['and',gate(0),gate(1)],['xor',gate(1),gate(2)],['or',gate(3),gate(4)],
             ['xor',gate(0),inp(6)],['and',gate(6),inp(7)],['or',gate(5),gate(7)],['xor',gate(8),inp(9)]]
    fanout=[['xor',inp(0),inp(1)],['and',gate(0),inp(2)],['or',gate(0),inp(3)],
            ['xor',gate(0),inp(4)],['and',gate(0),inp(5)],['or',gate(1),gate(2)],
            ['xor',gate(3),gate(4)],['and',gate(5),inp(6)],['or',gate(6),inp(7)],['xor',gate(7),gate(8)]]
    return {'chain':(9,chain),'diamond':(10,diamond),'fanout':(8,fanout)}

def main(dst):
    root=Path(dst);root.mkdir(parents=True,exist_ok=False);models={};targets=[];transforms=[];attacks=[]
    for name,(I,gates) in fixtures().items():
        models[name]={'inputs':I,'gates':gates};src=root/(name+'-plain.wasm');p.save(p.plain(I,gates),src)
        assert p.source(src)==(I,gates)
        variants={'plain':src}
        for label,mode,gauge in [('dag','dag',False),('dag-gauge','dag',True),('lex-gauge','lex',True),('flat-gauge','flat',True)]:
            out=root/(name+'-'+label+'.wasm');r=p.transform(src,out,mode,gauge)
            transforms.append({'name':name,'mode':label,**r});variants[label]=out
        for label,raw in variants.items():
            opt=raw.with_stem(raw.stem+'-O3');p.w.tool('wasm-opt',[raw,'-O3','-o',opt])
            for stage,binary in [('raw',raw),('O3',opt)]:
                p.w.tool('wasm-validate',[binary]);targets.append({'name':name,'mode':label,'stage':stage,'file':binary.name,'negative':label.startswith('flat')})
                if label not in ('plain','flat-gauge'):
                    out=binary.with_stem(binary.stem+'-recovered');r=p.recover(binary,out)
                    attacks.append({'file':binary.name,**r});targets.append({'name':name,'mode':label+'-recovered','stage':stage,'file':out.name,'negative':False})
    manifest={'models':models,'targets':targets,'transforms':transforms,'attacks':attacks}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    r=subprocess.run(['node',str(p.HERE/'check.cjs'),str(root)],capture_output=True,text=True,timeout=120)
    (root/'check-stdout.txt').write_text(r.stdout,encoding='utf8');(root/'check-stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    checks=json.loads(r.stdout);(root/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
    for file in ('prototype.py','run.py','check.cjs','plan.md'):shutil.copyfile(p.HERE/file,root/('source-'+file))
    shutil.copyfile(p.HERE.parent/'connectivity-elimination/prototype.py',root/'source-wat-helper.py')
    pins={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()}
    (root/'pins.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
    print(json.dumps({'conditions':len(targets),'positive_calls':sum(x['calls'] for x in checks['rows'] if not x['negative']),'recoveries':len(attacks),'negative_counterexamples':sum(x['mismatches']>0 for x in checks['rows'] if x['negative'])},indent=2))

if __name__=='__main__':main(sys.argv[1])
