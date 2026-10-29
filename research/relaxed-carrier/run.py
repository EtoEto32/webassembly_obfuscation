import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import statistics
import subprocess
import time
import tracemalloc
import prototype as p
HERE=Path(__file__).resolve().parent

def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def command(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120)
    if r.returncode:raise RuntimeError(json.dumps(dict(args=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return json.loads(r.stdout)
def kernel(name):
    c=p.c;g=p.get;o=p.op
    f=['func',['export','"run"'],['param','i32','i32','i32'],['result','i32']]
    if name=='majority':f.append(o('i32.or',o('i32.and',g(0),g(1)),o('i32.and',g(2),o('i32.or',g(0),g(1)))))
    else:
        f.append(['local','i32','i32'])
        for r in range(int(name[3:])):
            t=o('i32.xor',o('i32.xor',o('i32.xor',o('i32.and',g(0),g(1)),o('i32.rotl',g(2),c((r*7+3)&31))),c((r+1)*0x9e3779b9)),g(4))
            f += [['local.set','3',t],['local.set','0',o('i32.xor',g(1),o('i32.shr_u',g(3),c(r%5+1)))],['local.set','1',o('i32.or',g(2),o('i32.shl',g(3),c(r%3+1)))],['local.set','2',o('i32.xor',g(3),o('i32.rotl',g(0),c((r*3+5)&31)))],['local.set','4',o('i32.shr_u',g(3),c(7))]]
        f.append(o('i32.xor',o('i32.xor',g(0),g(1)),g(2)))
    return p.w.emit(['module',f])
def count(mod):
    f,ls,body=p.function(mod);n=0
    def walk(x):
        nonlocal n
        if isinstance(x,list):
            n+=1
            for a in x[1:]:walk(a)
    for x in body:walk(x)
    return dict(instruction_nodes=n,locals=len(ls),linear_memory_pages=0)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output');ap.add_argument('--compare');a=ap.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    snap=out/'sources';snap.mkdir();hashes={}
    for source in list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))+[HERE.parent/'connectivity-elimination/prototype.py']:
        shutil.copyfile(source,snap/(source.parent.name+'_'+source.name));hashes[str(source.relative_to(HERE.parents[1]))]=hashlib.sha256(source.read_bytes()).hexdigest()
    env=command(['node','-e',"console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require('os').cpus()[0].model,logical_cpus:require('os').cpus().length,arch:process.arch,platform:process.platform}))"])
    save(out/'environment.json',dict(env,python=platform.python_version(),os=platform.platform(),toolchain={'wabt':p.w.tool('wasm2wat',['--version']).strip(),'binaryen':p.w.tool('wasm-opt',['--version']).strip()},source_sha256=hashes))
    files=[];transforms=[];analysis=[]
    for name in ('majority','mix4','mix16'):
        plain=out/(name+'.plain.raw.wasm');p.compile_wat(kernel(name),plain)
        main=[dict(model=name,mode='plain',opt='raw',path=plain.name)]
        for mode in ('zero','dynamic','relaxed','ones','pattern'):
            path=out/(name+'.'+mode+'.raw.wasm');transforms.append(dict(path=path.name,**p.transform(plain,path,mode)));main.append(dict(model=name,mode=mode,opt='raw',path=path.name))
        for item in list(main):
            path=out/item['path'].replace('.raw.','.O3.');p.w.tool('wasm-opt',[out/item['path'],'-O3','--all-features','-o',path]);p.w.tool('wasm-validate',[path]);main.append(dict(item,path=path.name,opt='O3'))
        files+=main
        for item in main:
            if item['mode']!='relaxed':continue
            path=out/item['path'];target=out/(path.stem+'.recovered.wasm');r=p.recover(path,target)
            mod=p.read(path);samples=[]
            for _ in range(11):
                begin=time.perf_counter();p.simplify(mod);samples.append((time.perf_counter()-begin)*1000)
            tracemalloc.start();p.simplify(mod);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            analysis.append(dict(path=path.name,**r,simplify_samples_ms=samples,simplify_median_ms=statistics.median(samples),python_heap_peak_bytes=peak,recovered_bytes=target.stat().st_size))
            files.append(dict(item,path=target.name,kind='recovered'))
            files.append(dict(item,path=target.stem+'.refinement.wasm',kind='refinement'))
        print('built '+name,flush=True)
    save(out/'manifest.json',dict(files=files));save(out/'transforms.json',transforms);save(out/'analysis.json',analysis)
    correctness=command(['node',HERE/'check.cjs',out]);save(out/'correctness.json',correctness);print('correctness '+str(correctness['calls']),flush=True)
    targets=[f for f in files if f.get('kind')=='recovered' or ('kind' not in f and f['mode'] in ('plain','zero','dynamic','relaxed'))]
    tasks=[(f,r) for f in targets for r in range(3)];random.Random(20261019).shuffle(tasks);measure=[]
    for i,(f,r) in enumerate(tasks):
        measure.append(dict(path=f['path'],repeat=r,**command(['node',HERE/'bench.cjs',out/f['path']])))
        if i%20==0:print('benchmark '+str(i)+'/'+str(len(tasks)),flush=True)
    save(out/'benchmark.json',measure)
    summary=[]
    for f in files:
        samples=[x['median_ns'] for x in measure if x['path']==f['path']]
        summary.append(dict(f,bytes=(out/f['path']).stat().st_size,sha256=hashlib.sha256((out/f['path']).read_bytes()).hexdigest(),median_ns=statistics.median(samples) if samples else None,range_ns=[min(samples),max(samples)] if samples else None,**count(p.read(out/f['path']))))
    save(out/'summary.json',summary)
    if a.compare:
        prior=Path(a.compare);same={f['path']:(out/f['path']).read_bytes()==(prior/f['path']).read_bytes() for f in files};save(out/'replay.json',same)
        if not all(same.values()):raise AssertionError('Replay byte mismatch')
    print(json.dumps(dict(binaries=len(files),calls=correctness['calls'],mismatches=correctness['mismatches'],recoveries=len(analysis),benchmark_processes=len(measure))),flush=True)
if __name__=='__main__':main()
