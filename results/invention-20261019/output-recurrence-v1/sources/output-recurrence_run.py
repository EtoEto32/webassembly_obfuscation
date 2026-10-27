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
import prototype as p
HERE=Path(__file__).resolve().parent
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def command(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=120)
    if r.returncode:raise RuntimeError(json.dumps(dict(args=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return json.loads(r.stdout)
def models():
    rng=random.Random(20261019);base=dict(x0=rng.getrandbits(32),y0=rng.getrandbits(32),P=[rng.randrange(1,65536) for _ in range(6)],Q=[rng.randrange(1,65536) for _ in range(6)],R=[rng.randrange(1,65536) for _ in range(6)])
    return {'b'+str(b):dict(base,b=b) for b in (3,6,256,1<<31)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);out=a.output;snap=out/'sources';snap.mkdir();hashes={}
    for source in list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))+[HERE.parent/'connectivity-elimination/prototype.py']:
        shutil.copyfile(source,snap/(source.parent.name+'_'+source.name));hashes[str(source.relative_to(HERE.parents[1]))]=hashlib.sha256(source.read_bytes()).hexdigest()
    env=command(['node','-e',"console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require('os').cpus()[0].model,logical_cpus:require('os').cpus().length,arch:process.arch}))"])
    save(out/'environment.json',dict(env,python=platform.python_version(),os=platform.platform(),source_sha256=hashes,wabt=p.w.tool('wasm2wat',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip()))
    ds=models();files=[];transforms=[];analysis=[]
    for name,d in ds.items():
        src=out/(name+'.source.raw.wasm');p.compile_wat(p.wat(d,'source'),src);history=out/(name+'.history.raw.wasm');transforms.append(dict(model=name,**p.transform(src,history)))
        q=out/(name+'.quotient.raw.wasm');p.compile_wat(p.wat(p.quotient(d),'quotient'),q)
        main=[dict(model=name,mode=mode,opt='raw',path=name+'.'+mode+'.raw.wasm') for mode in ('source','history','quotient')]
        for f in list(main):
            opt=out/f['path'].replace('.raw.','.O3.');p.w.tool('wasm-opt',[out/f['path'],'-O3','--enable-multimemory','-o',opt]);p.w.tool('wasm-validate',[opt]);main.append(dict(f,path=opt.name,opt='O3'))
        files+=main
        for f in main:
            if f['mode']!='history':continue
            target=out/(Path(f['path']).stem+'.recovered.wasm');r=p.recover(out/f['path'],target);samples=[]
            for _ in range(11):
                begin=time.perf_counter();rep,_=p.extract(out/f['path'],out,'history');samples.append((time.perf_counter()-begin)*1000)
            same=target.read_bytes()==q.read_bytes();assert same
            analysis.append(dict(path=f['path'],**r,extract_validate_samples_ms=samples,extract_validate_median_ms=statistics.median(samples),same_as_quotient_bytes=same));files.append(dict(f,path=target.name,kind='recovered'))
        print('built '+name,flush=True)
    save(out/'manifest.json',dict(models=ds,files=files));save(out/'transforms.json',transforms);save(out/'analysis.json',analysis)
    check=command(['node',HERE/'check.cjs',out]);save(out/'correctness.json',check);print('correctness '+str(check['calls']),flush=True)
    # Separate native processes and serial timing; no concurrent heavy work.
    tasks=[(f,i) for f in files if 'kind' not in f for i in range(3)];random.Random(20261019).shuffle(tasks);bench=[]
    for i,(f,r) in enumerate(tasks):
        bench.append(dict(path=f['path'],repeat=r,**command(['node',HERE/'bench.cjs',out/f['path']])))
        if i%18==0:print('benchmark '+str(i)+'/'+str(len(tasks)),flush=True)
    save(out/'benchmark.json',bench);summary=[]
    for f in files:
        values=[r['median_ns'] for r in bench if r['path']==f['path']]
        summary.append(dict(f,bytes=(out/f['path']).stat().st_size,sha256=hashlib.sha256((out/f['path']).read_bytes()).hexdigest(),median_ns=statistics.median(values) if values else None,range_ns=[min(values),max(values)] if values else None,public_pages=1,private_pages=1))
    save(out/'summary.json',summary)
    if a.compare:
        same={f['path']:(out/f['path']).read_bytes()==(a.compare/f['path']).read_bytes() for f in files};save(out/'replay.json',same);assert all(same.values())
    print(json.dumps(dict(binaries=len(files),calls=check['calls'],traps=check['traps'],mismatches=0,recoveries=len(analysis),fresh_processes=len(bench))),flush=True)
if __name__=='__main__':main()
