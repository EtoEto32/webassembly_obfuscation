# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import prototype as p
import attack


def write(path,x):Path(path).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def ev(t,a):
    if t[0]=='var':return a[t[1]]
    if t[0]=='const':return t[1]&p.MASK
    x,y=ev(t[1],a),ev(t[2],a)
    return {'and':lambda:x&y,'or':lambda:x|y,'xor':lambda:x^y}[t[0]]()


def scalar(record,assignment):
    def row(pairs):
        v=0
        for mono,bits in pairs:
            if assignment & mono == mono:v ^= bits
        return v
    basis={}
    for pairs in record['rows']:
        v=row(pairs)
        while v:
            j=v.bit_length()-1
            if j not in basis:basis[j]=v;break
            v ^= basis[j]
    target=row(record['target'])
    while target:
        j=target.bit_length()-1
        if j not in basis:return 0
        target ^= basis[j]
    return 1


def main(mainpath,iopath,peelpath,perfpath,out):
    mainpath,iopath,peelpath,perfpath,out=map(Path,(mainpath,iopath,peelpath,perfpath,out))
    out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
    for name in ('audit.py','audit.cjs','prototype.py','attack.py'):
        shutil.copyfile(p.HERE/name,out/'sources'/name)
    checks={'pins_checked':0,'replays':[],'interpreter':[],'model_cases':0,'model_assignments':0,'source_rejections':[]}
    for base in (mainpath,iopath,peelpath,perfpath):
        pins=json.loads((base/'sha256.json').read_text(encoding='utf8'))
        for file,h in pins.items():
            assert hashlib.sha256((base/file).read_bytes()).hexdigest()==h
            checks['pins_checked']+=1
    manifest=json.loads((mainpath/'manifest.json').read_text(encoding='utf8'))
    audit={'targets':[],'probes':[]};engine_targets=[]
    for name,f in manifest['fixtures'].items():
        sub=out/name;sub.mkdir()
        plain=sub/'plain.wasm';p.save(p.w.plain_wat(f['n'],'"run"',f['tree']),plain)
        for mode in ('plain','span','constant','dependent'):
            dest=plain
            if mode!='plain':dest=sub/(mode+'.wasm');p.transform(plain,dest,mode)
            opt=dest.with_stem(dest.stem+'-O3');p.optimize(dest,opt)
            for form,file in (('raw',dest),('O3',opt)):
                original=mainpath/name/(mode+('-O3' if form=='O3' else '')+'.wasm')
                assert file.read_bytes()==original.read_bytes();checks['replays'].append(str(original))
                engine_targets.append((file,f))
            if mode=='dependent':
                rec,_=p.construct(f['n'],f['tree'],mode)
                blob,_,inp,_,_,basis,pages=p.layout(rec)
                for form in ('raw','O3'):
                    probe=sub/('probe-'+form+'.wasm')
                    if form=='raw':p.save(p.render(rec,probe=True),probe)
                    else:p.optimize(sub/'probe-raw.wasm',probe)
                    audit['probes'].append({'file':str(probe.resolve()),**f,'blob_bytes':len(blob),'scratch_start':inp,'scratch_end':basis+4*rec['d']**2})
        for mode in ('plain','span','constant','dependent','recovered'):
            file=perfpath/(name+'-'+mode+'-bench.wasm')
            audit['targets'].append({'file':str(file.resolve()),**f})
        for mode in ('plain','span','constant','dependent'):
            file=iopath/(name+'-'+mode+'-recovered.wasm')
            audit['targets'].append({'file':str(file.resolve()),**f});engine_targets.append((file,f))
        for mode in ('constant','dependent'):
            file=peelpath/(name+'-'+mode+'-recovered.wasm')
            if file.exists():audit['targets'].append({'file':str(file.resolve()),**f});engine_targets.append((file,f))
    # Independent scalar highest-pivot elimination on small random formulae.
    rng=random.Random(20261023)
    def tree(depth):
        if depth==0:return ('const',rng.choice([0,p.MASK])) if rng.randrange(5)==0 else ('var',rng.randrange(4))
        return (rng.choice(['and','or','xor']),tree(depth-1),tree(depth-1))
    small=[('const',0),('const',p.MASK),('var',0),('xor',('var',0),('var',1))]+[tree(2) for _ in range(20)]
    for i,t in enumerate(small):
        for mode in ('span','constant','dependent'):
            rec,_=p.construct(4,t,mode)
            for x in range(16):
                a=[p.MASK if x>>j&1 else 0 for j in range(4)]
                assert scalar(rec,x)==bool(ev(t,a));checks['model_assignments']+=1
            checks['model_cases']+=1
            if i<4:
                file=out/f'edge-{i}-{mode}.wasm';p.save(p.render(rec),file)
                audit['targets'].append({'file':str(file.resolve()),'n':4,'tree':t})
    for index,(file,f) in enumerate(engine_targets):
        mod=p.w.parse(p.w.tool('wasm2wat',[file,'--fold-exprs']))
        rows=[[0]*f['n'],[p.MASK]*f['n'],[(0x55555555 if j%2 else 0xaaaaaaaa) for j in range(f['n'])],[rng.getrandbits(32) for _ in range(f['n'])]]
        for j,a in enumerate(rows):
            mod.append(['func',['export',f'"probe{j}"'],['result','i32'],['call','0']+[['i32.const',str(x)] for x in a]])
        probe=out/f'interpreter-{index}.wasm';p.save(p.w.emit(mod),probe)
        text=p.w.tool('wasm-interp',[probe,'--run-all-exports'])
        (out/f'interpreter-{index}.txt').write_text(text,encoding='utf8')
        got=[int(v)&p.MASK for v in re.findall(r'probe\d+\(\) => i32:(\d+)',text)]
        expected=[ev(f['tree'],a)&p.MASK for a in rows]
        if got!=expected:raise AssertionError((file,text,expected))
        checks['interpreter'].append({'file':str(file),'results':got,'calls':4})
    write(out/'audit-manifest.json',audit)
    r=subprocess.run(['node',str(p.HERE/'audit.cjs'),str(out)],capture_output=True,text=True,timeout=120)
    (out/'node.stdout.txt').write_text(r.stdout,encoding='utf8');(out/'node.stderr.txt').write_text(r.stderr,encoding='utf8')
    if r.returncode:raise RuntimeError(r.stderr)
    write(out/'audit.json',checks)
    write(out/'sha256.json',{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()})
    print(json.dumps({'pins_checked':checks['pins_checked'],'replays':len(checks['replays']),'interpreter_calls':sum(x['calls'] for x in checks['interpreter']),'model_cases':checks['model_cases'],'model_assignments':checks['model_assignments'],'node':json.loads(r.stdout)}))


if __name__=='__main__':main(*sys.argv[1:])
