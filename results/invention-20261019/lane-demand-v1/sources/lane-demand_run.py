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
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def command(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=60)
    if r.returncode:raise RuntimeError(json.dumps(dict(args=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return json.loads(r.stdout)
def models():
    x,y=p.get(0),p.get(1);data={'diamond':['i32.add',['i32.mul',['i32.add',x,y],['i32.sub',x,y]],['i32.xor',x,y]]}
    for rounds in (1,4,8):
        expr=x
        for i in range(rounds):expr=['i32.xor',['i32.rotl',['i32.add',['i32.mul',expr,p.const(0x45d9f3b+2*i)],y],p.const((i*7+3)%31+1)],p.const(0x9e3779b9^i)]
        data['mix'+str(rounds)]=expr
    return data
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=False);snapshot=out/'sources';snapshot.mkdir();hashes={}
    sources=list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))+[HERE.parent/'output-recurrence/prototype.py',HERE.parent/'connectivity-elimination/prototype.py']
    for source in sources:
        hashes[str(source.relative_to(HERE.parents[1]))]=hashlib.sha256(source.read_bytes()).hexdigest();shutil.copyfile(source,snapshot/(source.parent.name+'_'+source.name))
    env=command(['node','-e',"console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:require('os').cpus()[0].model,arch:process.arch}))"])
    save(out/'environment.json',dict(env,python=platform.python_version(),os=platform.platform(),wabt=p.w.tool('wasm2wat',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip(),source_sha256=hashes))
    ds=models();files=[];transforms=[];attacks=[]
    for name,expr in ds.items():
        source=out/(name+'.source.raw.wasm');p.compile_wat(p.scalar_module(expr),source)
        for mode in ('source','vector','static','dynamic'):
            path=out/(name+'.'+mode+'.raw.wasm')
            if mode!='source':transforms.append(dict(model=name,mode=mode,**p.transform(source,path,mode)))
            for opt in ('raw','O3'):
                target=path if opt=='raw' else path.with_name(path.name.replace('.raw.','.O3.'))
                if opt=='O3':p.w.tool('wasm-opt',[path,'-O3','--enable-simd','-o',target]);p.w.tool('wasm-validate',[target])
                row=dict(model=name,mode=mode,opt=opt,path=target.name);files.append(row)
                if mode=='source':continue
                recovered=out/(target.stem+'.recovered.wasm')
                try:
                    stats=attack.recover(target,recovered);rep=[]
                    root=p.expanded(target,allow_vector=True)
                    for _ in range(7):
                        start=time.perf_counter();attack.scalarize(root);rep.append((time.perf_counter()-start)*1000)
                    attacks.append(dict(row,status='recovered',samples_ms=rep,median_scalarize_ms=statistics.median(rep),**stats));files.append(dict(row,path=recovered.name,kind='recovered'))
                except ValueError as error:attacks.append(dict(row,status='unsupported',reason=str(error)))
        print('built '+name,flush=True)
    save(out/'manifest.json',dict(models=ds,files=files));save(out/'transforms.json',transforms);save(out/'attacks.json',attacks)
    check=command(['node',HERE/'check.cjs',out]);save(out/'correctness.json',check);print('correctness '+str(check['calls']),flush=True)
    tasks=[(f,i) for f in files if 'kind' not in f for i in range(3)];random.Random(20261019).shuffle(tasks);bench=[]
    for count,(f,i) in enumerate(tasks):
        bench.append(dict(path=f['path'],repeat=i,**command(['node',HERE/'bench.cjs',out/f['path']])))
        if count%24==0:print('bench '+str(count),flush=True)
    save(out/'benchmark.json',bench);summary=[]
    for f in files:
        values=[r['median_ns'] for r in bench if r['path']==f['path']];data=(out/f['path']).read_bytes();summary.append(dict(f,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),median_ns=statistics.median(values) if values else None,range_ns=[min(values),max(values)] if values else None))
    save(out/'summary.json',summary)
    if a.compare:
        replay={f['path']:(out/f['path']).read_bytes()==(a.compare/f['path']).read_bytes() for f in files};save(out/'replay.json',replay);assert all(replay.values())
    print(json.dumps(dict(binaries=len(files),calls=check['calls'],recovered=sum(r['status']=='recovered' for r in attacks),unsupported=sum(r['status']=='unsupported' for r in attacks),fresh_processes=len(bench))))
if __name__=='__main__':main()
