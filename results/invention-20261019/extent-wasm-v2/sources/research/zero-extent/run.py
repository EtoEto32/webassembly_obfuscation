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
import models
HERE=Path(__file__).resolve().parent
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def command(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180)
    if r.returncode:raise RuntimeError(json.dumps(dict(command=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return r.stdout
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=dict(files=[]);transforms=[];analysis=[]
    for name,body in models.models().items():
        src=out/(name+'.plain.raw.wasm');p.compile_wat(p.w.emit(models.module(body)),src)
        for mode in ('plain','flat','extent','explicit'):
            raw=out/(name+'.'+mode+'.raw.wasm')
            if mode!='plain':transforms.append(dict(model=name,**p.transform(src,raw,mode)))
            for opt in ('raw','O2','O3'):
                target=raw if opt=='raw' else out/(name+'.'+mode+'.'+opt+'.wasm')
                if opt!='raw':p.w.tool('wasm-opt',[raw,'-'+opt,'--enable-bulk-memory','-o',target])
                item=dict(path=target.name,model=name,mode=mode,opt=opt,recovered=False);manifest['files'].append(item)
                t=time.perf_counter();m,_,_=p.read(target);parse=(time.perf_counter()-t)*1000;samples=[]
                for _ in range(11):
                    t=time.perf_counter();normalized,stats=p.normalize(m);samples.append((time.perf_counter()-t)*1000)
                tracemalloc.start();p.normalize(m);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
                dst=out/(target.stem+'.recovered.wasm');p.compile_wat(p.w.emit(normalized),dst)
                manifest['files'].append(dict(item,path=dst.name,recovered=True))
                analysis.append(dict(item,status='success',parse_ms=parse,samples_ms=samples,peak_python_bytes=peak,**stats,
                                     original_ifs=sum(x[0]=='if' for x in p.nodes(m)),recovered_ifs=sum(x[0]=='if' for x in p.nodes(normalized))))
    save(out/'manifest.json',manifest);save(out/'transforms.json',transforms);save(out/'analysis.json',analysis)
    checks=json.loads(command(['node',HERE/'check.cjs',out]));save(out/'checks.json',checks);print(json.dumps(checks|{'rows':'saved'}),flush=True)
    mains=[x for x in manifest['files'] if not x['recovered']];order=[(x,pattern) for x in mains for pattern in ('mixed','zero','one') for _ in range(3)]
    random.Random(20261019).shuffle(order);bench=[]
    for i,(item,pattern) in enumerate(order):
        bench.append(dict(path=item['path'],process=i,**json.loads(command(['node',HERE/'bench.cjs',out/item['path'],pattern]))))
    save(out/'benchmark.json',bench);summary=[]
    for item in mains:
        for pattern in ('mixed','zero','one'):
            rows=[x for x in bench if x['path']==item['path'] and x['pattern']==pattern];ms=[statistics.median(x['samples_ns']) for x in rows]
            summary.append(dict(item,pattern=pattern,bytes=(out/item['path']).stat().st_size,median_ns=statistics.median(ms),min_ns=min(ms),max_ns=max(ms),
                                public_memory_bytes=rows[0]['public_memory_bytes'],max_rss_kib=max(x['max_rss_kib'] for x in rows)))
    save(out/'summary.json',summary);hashes={}
    for src in list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))+[Path(p.w.__file__)]:
        name=src.relative_to(p.w.ROOT).as_posix();hashes[name]=hashlib.sha256(src.read_bytes()).hexdigest();dst=out/'sources'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),node=bench[0]['node'],v8=bench[0]['v8'],cpu=bench[0]['cpu'],
                                   wabt=p.w.tool('wasm-validate',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip(),source_hashes=hashes))
    if a.compare:
        for item in manifest['files']:assert (out/item['path']).read_bytes()==(a.compare/item['path']).read_bytes()
        save(out/'replay.json',dict(identical=len(manifest['files'])))
    print(json.dumps(dict(done=True,binaries=len(manifest['files']),processes=len(bench))),flush=True)
if __name__=='__main__':main()
