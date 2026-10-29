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
def save(path,obj):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def command(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120)
    if r.returncode:raise RuntimeError(json.dumps(dict(args=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return json.loads(r.stdout)
def wat(rows):
    return p.s.plain([[r[a] for r in rows]+[0]*(16-len(rows)) for a in range(2)],sum(r[2]<<i for i,r in enumerate(rows)))
def models():
    out={}
    for n in (4,8,16):out['cycle'+str(n)]=[[(q+1)%n,(q+2)%n,int(q==0)] for q in range(n)]
    rng=random.Random(20261019)
    for _ in range(1000):
        rows=[[rng.randrange(8),rng.randrange(8),rng.randrange(2)] for q in range(8)]
        small,_=p.quotient(rows)
        if len(small)==8:out['general8']=small;break
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output');ap.add_argument('--compare');a=ap.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    source=models();files=[];analysis=[];learning=[];transforms=[]
    snapshot=out/'sources';snapshot.mkdir();hashes={}
    sources=list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))+[HERE.parent/'suffix-transport/prototype.py',HERE.parent/'connectivity-elimination/prototype.py',HERE.parent/'overlap-automata/check.cjs']
    for f in sources:
        name=f.parent.name+'_'+f.name;shutil.copyfile(f,snapshot/name);hashes[str(f.relative_to(HERE.parents[1]))]=hashlib.sha256(f.read_bytes()).hexdigest()
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),source_sha256=hashes,toolchain={'wabt':'1.0.42','binaryen':'133'}))
    for name,rows in source.items():
        plain=out/(name+'.plain.raw.wasm');p.compile_wat(wat(rows),plain)
        main=[dict(model=name,mode='plain',opt='raw',path=plain.name,private_pages=0)]
        for k in (1,16,256,2048):
            target=out/(name+'.lift'+str(k)+'.raw.wasm');r=p.transform(plain,target,k);transforms.append(dict(path=target.name,**r));main.append(dict(model=name,mode='lift'+str(k),opt='raw',path=target.name,private_pages=r['private_pages']))
        for item in list(main):
            optimized=out/item['path'].replace('.raw.','.O3.');p.w.tool('wasm-opt',[out/item['path'],'-O3','--enable-multimemory','-o',optimized]);p.w.tool('wasm-validate',[optimized,'--enable-multi-memory']);main.append(dict(item,path=optimized.name,opt='O3'))
        files+=main
        for item in main:
            target=out/item['path']
            if item['mode']!='plain':
                full,start,ex=p.extract(target,out);times=[]
                for _ in range(9):
                    begin=time.perf_counter();small,stats=p.quotient(full,start);times.append((time.perf_counter()-begin)*1000)
                tracemalloc.start();p.quotient(full,start);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
                eq=p.equivalent(rows,small)
                if not eq['equivalent']:raise AssertionError(eq)
                recovered=target.with_name(target.stem+'.static.wasm');p.compile_wat(wat(small),recovered);files.append(dict(item,path=recovered.name,kind='static_recovery'))
                analysis.append(dict(path=target.name,**ex,**stats,analysis_ms=statistics.median(times),samples_ms=times,python_heap_peak_bytes=peak,**eq))
            result=command(['node',HERE/'learn.cjs',target]);eq=p.equivalent(rows,result['rows']);learning.append(dict(path=target.name,**result,posthoc_manager_equivalence=eq))
            if eq['equivalent']:
                clone=target.with_name(target.stem+'.learned.wasm');p.compile_wat(wat(result['rows']),clone);files.append(dict(item,path=clone.name,kind='public_learning'))
            print('checked '+target.name,flush=True)
    save(out/'transforms.json',transforms);save(out/'static-analysis.json',analysis);save(out/'public-learning.json',learning)
    # A long, rare exception: finite oracle testing must not be treated as proof.
    word='0'*31+'1';rare=[];reject=len(word)+1
    for i,c in enumerate(word):rare.append([i+1 if c==str(a) else reject for a in range(2)]+[0])
    rare.append([reject,reject,1]);rare.append([reject,reject,0]);rarebin=out/'rare-exception.wasm';p.compile_wat(p.table_wat(rare,0),rarebin)
    negative=command(['node',HERE/'learn.cjs',rarebin]);negative['posthoc_manager_equivalence']=p.equivalent(rare,negative['rows']);save(out/'rare-control.json',negative)
    if negative['posthoc_manager_equivalence']['equivalent']:raise AssertionError('Control unexpectedly learned; revisit negative test')
    manifest=dict(models={name:dict(trans=[r[:2] for r in rows],start=0,final=sum(r[2]<<i for i,r in enumerate(rows))) for name,rows in source.items()},files=files)
    save(out/'manifest.json',manifest);check=command(['node',HERE.parent/'overlap-automata/check.cjs',out]);save(out/'correctness.json',check)
    print('correctness '+str(check),flush=True)
    # Serial benchmark processes; do not run other experiments concurrently.
    tasks=[(f,i) for f in files if 'kind' not in f for i in range(3)];random.Random(20261019).shuffle(tasks);measurements=[]
    for num,(f,i) in enumerate(tasks):
        r=command(['node',HERE/'bench.cjs',out/f['path']]);measurements.append(dict(path=f['path'],repeat=i,**r))
        if num%20==0:print('benchmark '+str(num)+'/'+str(len(tasks)),flush=True)
    save(out/'benchmark.json',measurements)
    summary=[]
    for f in files:
        if 'kind' in f:continue
        values=[r['median_ns'] for r in measurements if r['path']==f['path']]
        summary.append(dict(f,bytes=(out/f['path']).stat().st_size,median_ns=statistics.median(values),range_ns=[min(values),max(values)]))
    save(out/'summary.json',summary)
    if a.compare:
        compare=Path(a.compare);matches={f['path']:hashlib.sha256((out/f['path']).read_bytes()).hexdigest()==hashlib.sha256((compare/f['path']).read_bytes()).hexdigest() for f in files};save(out/'replay.json',matches)
        if not all(matches.values()):raise AssertionError('Replay mismatch')
    print(json.dumps(dict(main_conditions=len(summary),binaries=len(files),correctness=check,static=len(analysis),public_learning=len(learning),learning_equivalent=sum(r['posthoc_manager_equivalence']['equivalent'] for r in learning),negative_control=negative['posthoc_manager_equivalence'])),flush=True)

if __name__=='__main__':main()
