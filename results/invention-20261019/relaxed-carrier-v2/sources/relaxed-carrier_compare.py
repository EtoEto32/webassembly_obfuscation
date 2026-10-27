"""Known-family mask specialization and optimizer-only controls."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time
import tracemalloc
import prototype as p
from run import save,command

def dynamic(mod):
    # Conditional recovery for this known mask-independent family. This is not
    # an arbitrary-program rewrite or a verifier of mask independence.
    f,ls,body=p.function(mod);found=0
    pattern=p.op('i32.xor',p.get(0),p.op('i32.rotl',p.get(1),p.c(7)))
    def walk(x):
        nonlocal found
        if x[0] not in p.PURE:raise ValueError('Outside pure scope')
        if x==pattern:found+=1;return p.c(0)
        return [walk(v) if isinstance(v,list) else v for v in x]
    fresh=[walk(x) for x in body]
    header=[x for x in f[1:] if isinstance(x,list) and x[0] in ('type','param','result','local')]
    return ['module',*[(['func',*header,*fresh] if x is f else x) for x in mod[1:]]],found

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    main=json.loads((a.input/'manifest.json').read_text())['files'];files=[];analysis=[]
    for item in main:
        if 'kind' in item or item['mode'] not in ('plain','dynamic','relaxed'):continue
        source=a.input/item['path'];mod=p.read(source)
        # All three modes receive the same converging optimizer budget.
        optimized=a.output/(source.stem+'.converged.wasm');begin=time.perf_counter();p.w.tool('wasm-opt',[source,'-O3','--converge','--all-features','-o',optimized]);p.w.tool('wasm-validate',[optimized]);optimizer_ms=(time.perf_counter()-begin)*1000
        files.append(dict(item,path=optimized.name,kind='optimizer_only'))
        if item['mode']=='plain':continue
        fun=dynamic if item['mode']=='dynamic' else p.simplify;samples=[]
        for _ in range(11):
            begin=time.perf_counter();reduced,count=fun(mod);samples.append((time.perf_counter()-begin)*1000)
        if count!=1:raise AssertionError((item,count))
        tracemalloc.start();fun(mod);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        target=a.output/(source.stem+'.specialized.wasm');begin=time.perf_counter();p.compile_wat(p.w.emit(reduced),target)
        final=a.output/(source.stem+'.recovered.wasm');p.w.tool('wasm-opt',[target,'-O3','--converge','--all-features','-o',final]);p.w.tool('wasm-validate',[final]);build_ms=(time.perf_counter()-begin)*1000
        files+=[dict(item,path=target.name,kind='specialized'),dict(item,path=final.name,kind='recovered')]
        analysis.append(dict(path=item['path'],mode=item['mode'],model=item['model'],opt=item['opt'],analysis_median_ms=statistics.median(samples),samples_ms=samples,python_heap_peak_bytes=peak,build_validate_optimize_ms=build_ms,optimizer_only_ms=optimizer_ms,source_bytes=source.stat().st_size,optimizer_only_bytes=optimized.stat().st_size,recovered_bytes=final.stat().st_size))
    save(a.output/'manifest.json',dict(files=files));save(a.output/'analysis.json',analysis)
    correctness=command(['node',Path(__file__).with_name('check.cjs'),a.output]);save(a.output/'correctness.json',correctness)
    # Unmodified public-output control disproves unconditional dynamic zeroing.
    direct=['module',['func',['export','"run"'],['param','i32','i32','i32'],['result','i32'],p.op('i32.xor',p.get(0),p.op('i32.rotl',p.get(1),p.c(7)))]]
    p.compile_wat(p.w.emit(direct),a.output/'observable-dynamic.wasm');reduced,count=dynamic(p.read(a.output/'observable-dynamic.wasm'));p.compile_wat(p.w.emit(reduced),a.output/'observable-dynamic-reduced.wasm')
    witness=command(['node','-e',"const fs=require('fs');console.log(JSON.stringify(process.argv.slice(1).map(p=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(p))).exports.run(1,2,3))));",a.output/'observable-dynamic.wasm',a.output/'observable-dynamic-reduced.wasm'])
    assert witness[0]!=witness[1];save(a.output/'conditional-recovery-control.json',dict(input=[1,2,3],observed=witness,conclusion='Mask independence is a necessary precondition, not checked by this family-specific attacker.'))
    save(a.output/'script-hashes.json',{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(__file__),Path(p.__file__),Path(__file__).with_name('check.cjs'))})
    print(json.dumps(dict(binaries=len(files),calls=correctness['calls'],mismatches=correctness['mismatches'],adaptive_conditions=len(analysis))))
if __name__=='__main__':main()
