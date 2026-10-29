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
import attack

HERE=Path(__file__).resolve().parent


def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)


def command(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=60)
    if r.returncode:raise RuntimeError(json.dumps(dict(args=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return json.loads(r.stdout)


def models():
    x,y=p.get(0),p.get(1)
    square=['i32.mul',x,x]
    ds={'cubic':['i32.add',['i32.mul',square,x],['i32.mul',p.const(5),y]],
        'quartic':['i32.add',['i32.mul',square,square],y],
        'bivar':['i32.sub',['i32.mul',['i32.add',x,y],['i32.mul',x,y]],['i32.mul',y,y]]}
    for rounds in (4,8):
        e=x
        for i in range(rounds):e=['i32.add',['i32.mul',e,['i32.add',e,p.const(3+2*i)]],['i32.add',['i32.mul',x,y],p.const(0x9e3779b9+i*2)]]
        ds['iter'+str(rounds)]=e
    return ds


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--no-bench',action='store_true');ap.add_argument('--compare',type=Path);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=False);snapshot=out/'sources';snapshot.mkdir();hashes={}
    sources=list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))+[HERE.parent/'lane-demand/prototype.py',HERE.parent/'lane-demand/check.cjs',HERE.parent/'output-recurrence/prototype.py',HERE.parent/'connectivity-elimination/prototype.py']
    for source in sources:
        hashes[str(source.relative_to(HERE.parents[1]))]=hashlib.sha256(source.read_bytes()).hexdigest();shutil.copyfile(source,snapshot/(source.parent.name+'_'+source.name))
    env=command(['node','-e',"console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require('os').cpus()[0].model,arch:process.arch}))"])
    save(out/'environment.json',dict(env,python=platform.python_version(),os=platform.platform(),wabt=p.w.tool('wasm2wat',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip(),source_sha256=hashes))
    ds=models();files=[];transforms=[];attacks=[]
    for name,expr in ds.items():
        src=out/(name+'.source.raw.wasm');p.compile_wat(p.scalar_dag(expr),src)
        for mode in ('source','diagonal','constant','dynamic'):
            raw=out/(name+'.'+mode+'.raw.wasm')
            if mode!='source':transforms.append(dict(model=name,mode=mode,**p.transform(src,raw,mode)))
            for opt in ('raw','O3'):
                path=raw if opt=='raw' else out/(name+'.'+mode+'.O3.wasm')
                if opt=='O3':p.w.tool('wasm-opt',[raw,'-O3','--enable-simd','-o',path]);p.w.tool('wasm-validate',[path])
                row=dict(model=name,mode=mode,opt=opt,path=path.name);files.append(row)
                if mode=='source':continue
                recovered=out/(path.stem+'.recovered.wasm')
                try:
                    stats=attack.recover(path,recovered);root=p.expanded(path,allow_vector=True);samples=[]
                    for _ in range(9):
                        begin=time.perf_counter();attack.project(root);samples.append((time.perf_counter()-begin)*1000)
                    attacks.append(dict(row,status='recovered',median_ms=statistics.median(samples),samples_ms=samples,**stats));files.append(dict(row,kind='recovered',path=recovered.name))
                except ValueError as error:attacks.append(dict(row,status='unsupported',reason=str(error)))
        print('built '+name,flush=True)
    save(out/'manifest.json',dict(models=ds,files=files));save(out/'transforms.json',transforms);save(out/'attacks.json',attacks)
    correct=command(['node',HERE.parent/'lane-demand/check.cjs',out]);save(out/'correctness.json',correct);print('checked '+str(correct['calls']),flush=True)
    bench=[]
    if not a.no_bench:
        tasks=[(f,i) for f in files for i in range(3)];random.Random(20261019).shuffle(tasks)
        for count,(f,i) in enumerate(tasks):
            bench.append(dict(path=f['path'],repeat=i,**command(['node',HERE/'bench.cjs',out/f['path']])))
            if count%30==0:print('bench '+str(count),flush=True)
    save(out/'benchmark.json',bench);summary=[]
    for f in files:
        data=(out/f['path']).read_bytes();values=[b['median_ns'] for b in bench if b['path']==f['path']]
        summary.append(dict(f,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),median_ns=statistics.median(values) if values else None,range_ns=[min(values),max(values)] if values else None))
    save(out/'summary.json',summary)
    if a.compare:
        replay={f['path']:(out/f['path']).read_bytes()==(a.compare/f['path']).read_bytes() for f in files};save(out/'replay.json',replay);assert all(replay.values())
    print(json.dumps(dict(binaries=len(files),calls=correct['calls'],recovered=sum(r['status']=='recovered' for r in attacks),unsupported=sum(r['status']=='unsupported' for r in attacks),benchmark_processes=len(bench))))


if __name__=='__main__':main()
