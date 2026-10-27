"""Bounded gate, keeping inconclusive recovery separate from resistance."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import re
import shutil
import statistics
import subprocess
import time
import tracemalloc
import prototype as p

HERE=Path(__file__).resolve().parent
a=p.a


def save(path,x):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def command(cmd,timeout=180):
    result=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=timeout)
    if result.returncode:raise RuntimeError(json.dumps(dict(command=list(map(str,cmd)),stdout=result.stdout,stderr=result.stderr)))
    return result.stdout
def models():
    x=[a.var(i) for i in range(5)];u=x[4]
    shift1=a.add(a.add(a.mul(x[0],x[1]),a.scale(x[2],3)),a.add(x[3],u))
    shift2=a.add(a.add(a.mul(x[0],x[0]),a.mul(x[1],x[2])),a.add(a.scale(x[3],5),a.mul(u,a.add(x[0],a.const(1)))))
    coupled=[a.add(a.add(a.mul(x[i],x[(i+1)%4]),a.scale(x[(i+2)%4],2*i+1)),a.add(a.scale(u,i+1),a.const(i+7))) for i in range(4)]
    return dict(shift_product=[shift1,x[0],x[1],x[2]],shift_square=[shift2,x[0],x[1],x[2]],coupled=coupled)
def value(poly,x):
    total=0
    for k,c in poly.items():
        v=c
        for i in k:v=v*x[i]&a.MASK
        total=total+v&a.MASK
    return total
def run_model(f,data):
    state=[0]*4
    for u in data:state=[value(poly,state+[u]) for poly in f]
    return state[0]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--smoke',action='store_true');ap.add_argument('--compare',type=Path)
    args=ap.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    ds=models();ds={k:v for k,v in ds.items() if not args.smoke or k=='shift_product'}
    manifest=dict(models={k:a.serial(v) for k,v in ds.items()},files=[]);analysis=[];transforms=[];model_checks=[]
    rng=random.Random(20261018)
    for name,f in ds.items():
        src=out/(name+'.plain.raw.wasm');p.s.compile_wat(p.scalar_wat(f),src)
        for mode in ('plain','identity','decode','fused'):
            raw=out/(name+'.'+mode+'.raw.wasm')
            if mode!='plain':transforms.append(dict(model=name,**p.transform(src,raw,mode)))
            for opt in ('raw','O2','O3'):
                target=raw if opt=='raw' else out/(name+'.'+mode+'.'+opt+'.wasm')
                if opt!='raw':p.w.tool('wasm-opt',[raw,'-'+opt,'--enable-simd','-o',target])
                item=dict(path=target.name,model=name,mode=mode,opt=opt,recovered=False);manifest['files'].append(item)
                try:
                    start=time.perf_counter();program=p.s.read(target);expanded,c=p.extract(program);extract_ms=(time.perf_counter()-start)*1000
                    trials=[];rec=None;report=None
                    for method,attack in [('linear_preimage',a.observe_recover),('known_factor',a.factor_recover)]:
                        start=time.perf_counter();candidate,trial=attack(expanded,c);trial.update(method=method,analysis_ms=(time.perf_counter()-start)*1000)
                        trials.append(trial)
                        if candidate is not None and rec is None:rec,report=candidate,dict(trial)
                    if report is None:report=dict(status='inconclusive');attack=a.observe_recover
                    else:attack=a.observe_recover if report['method']=='linear_preimage' else a.factor_recover
                    report['trials']=trials;samples=[]
                    for _ in range(11):
                        start=time.perf_counter();attack(expanded,c);samples.append((time.perf_counter()-start)*1000)
                    tracemalloc.start();attack(expanded,c);peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
                    report.update(path=target.name,extract_ms=extract_ms,samples_ms=samples,python_peak_bytes=peak,
                                  polynomial_terms=sum(map(len,expanded)),coefficients=a.serial(expanded),observation=c)
                    if rec is not None:
                        assert rec==f,(name,mode,opt,'Not recovered original canonical coordinates')
                        recovered=out/(target.stem+'.recovered.wasm');p.s.compile_wat(p.scalar_wat(rec),recovered)
                        manifest['files'].append(dict(item,path=recovered.name,recovered=True));report['exact_original_update']=True
                    analysis.append(report)
                except ValueError as error:analysis.append(dict(path=target.name,status='unsupported',reason=str(error)))
        # Algebra at arbitrary full-width states, independent of reachable inputs.
        matrix=a.basis(20261018);expanded,c=a.conjugate(f,matrix)
        for case in range(1024):
            x=[rng.getrandbits(32) for _ in range(4)];u=rng.getrandbits(32)
            z=[sum(k*v for k,v in zip(row,x))&a.MASK for row in matrix];fx=[value(poly,x+[u]) for poly in f]
            lhs=[value(poly,z+[u]) for poly in expanded];rhs=[sum(k*v for k,v in zip(row,fx))&a.MASK for row in matrix]
            assert lhs==rhs and sum(k*v for k,v in zip(c,z))&a.MASK==x[0]
        model_checks.append(dict(model=name,full_width_states=1024,mismatches=0))
        print(json.dumps(dict(generated=name)),flush=True)
    save(out/'manifest.json',manifest);save(out/'analysis.json',analysis);save(out/'transforms.json',transforms);save(out/'algebra-checks.json',model_checks)
    check=json.loads(command(['node',HERE/'check.cjs',out]));save(out/'checks.json',check);print(json.dumps(check),flush=True)
    # WABT interpreter: separate from Node, so SIMD checks do not depend
    # solely on V8's implementation of vector multiplication.
    folder=out/'interpreter';folder.mkdir();records=[];data=bytes([0,1,2,3,254,255,128,127])
    for item in manifest['files']:
        wat=p.w.tool('wasm2wat',[out/item['path'],'--fold-exprs','--no-debug-names'])
        tail='(data (i32.const 0) "'+''.join('\\%02x'%b for b in data)+'")'
        for i,n in enumerate([0,1,3,8]):tail+=f'(func (export "check{i}") (result i32) (call 0 (i32.const 0) (i32.const {n})))'
        target=folder/item['path'];p.s.compile_wat(wat.rstrip()[:-1]+tail+')',target)
        log=p.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf-8')
        got=[int(x) for x in re.findall(r'check\d+\(\) => i32:(\d+)',log)];expected=[run_model(ds[item['model']],data[:n]) for n in [0,1,3,8]]
        assert got==expected,(item,got,expected);records.append(dict(path=item['path'],got=got,expected=expected))
    save(out/'interpreter.json',dict(engine='WABT',calls=len(records)*4,mismatches=0,records=records))
    # Control/effect recognition must reject these valid Wasm programs.
    raw=out/(next(iter(ds))+'.fused.raw.wasm');wat=p.w.tool('wasm2wat',[raw,'--fold-exprs','--no-debug-names']);negatives=[]
    for kind,text in [('store',wat.replace('(local.set 3','(i32.store8 (i32.const 0) (i32.const 9)) (local.set 3',1)),
                      ('address',wat.replace('(i32.add','(i32.sub',1)),('guard',wat.replace('(i32.ge_u','(i32.gt_u',1))]:
        target=out/('negative-'+kind+'.wasm');p.s.compile_wat(text,target)
        try:p.extract(p.s.read(target));raise AssertionError('Accepted unsafe scanner: '+kind)
        except ValueError as e:negatives.append(dict(kind=kind,status='rejected',reason=str(e)))
    save(out/'negatives.json',negatives)
    order=[f for f in manifest['files'] if not f['recovered']]*3;rng.shuffle(order);bench=[]
    for i,item in enumerate(order):bench.append(dict(path=item['path'],process=i,**json.loads(command(['node',HERE/'bench.cjs',out/item['path']]))))
    save(out/'benchmark.json',bench);summary=[]
    for item in manifest['files']:
        if item['recovered']:continue
        rows=[r for r in bench if r['path']==item['path']];samples=[statistics.median(r['samples_ns']) for r in rows]
        summary.append(dict(item,bytes=(out/item['path']).stat().st_size,median_ns=statistics.median(samples),min_ns=min(samples),max_ns=max(samples),
                            public_memory_bytes=rows[0]['public_memory_bytes'],max_rss_kib=max(r['max_rss_kib'] for r in rows)))
    save(out/'summary.json',summary)
    sources=list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))+[Path(p.s.__file__),Path(p.w.__file__)];hashes={}
    for src in sources:
        rel=str(src.relative_to(p.w.ROOT)).replace('\\','/');hashes[rel]=hashlib.sha256(src.read_bytes()).hexdigest()
        dest=out/'sources'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),node=bench[0]['node'],v8=bench[0]['v8'],cpu=bench[0]['cpu'],
                                   wabt=p.w.tool('wasm-validate',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip(),source_hashes=hashes))
    if args.compare:
        for f in manifest['files']:assert (out/f['path']).read_bytes()==(args.compare/f['path']).read_bytes()
        save(out/'replay.json',dict(identical=len(manifest['files'])))
    print(json.dumps(dict(done=True,binaries=len(manifest['files']),status_counts={status:sum(x['status']==status for x in analysis) for status in set(x['status'] for x in analysis)})),flush=True)


if __name__=='__main__':main()
