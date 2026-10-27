"""End-to-end actual Wasm gate, with trap-visible prefix comparison."""
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


def save(path,obj):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')


def command(args):
    run=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180)
    if run.returncode:raise RuntimeError(json.dumps(dict(args=list(map(str,args)),stdout=run.stdout,stderr=run.stderr)))
    return run.stdout


def models():
    return dict(increasing=dict(params=5,stores=[(4*i,4,i+1) for i in range(4)]),
                descending=dict(params=5,stores=[(4*i,4,i+1) for i in reversed(range(4))]),
                zigzag=dict(params=9,stores=[(4*i,4,i+1) for i in [3,0,2,1,7,4,6,5]]),
                overlap=dict(params=7,stores=[(12,4,1),(0,4,2),(6,4,3),(3,4,4),(20,4,5),(14,4,6)]))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);args=ap.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);ds=models();manifest=dict(models=ds,files=[]);analysis=[];transforms=[]
    for name,model in ds.items():
        src=out/(name+'.plain.raw.wasm');p.compile_wat(p.plain(model['params'],model['stores']),src)
        params,ops=p.source(src);expected=p.signature(p.frontiers(ops))
        for mode in ('plain','byte','coalesced','woven0','woven1'):
            raw=out/(name+'.'+mode+'.raw.wasm')
            if mode!='plain':transforms.append(dict(model=name,**p.transform(src,raw,mode)))
            for opt in ('raw','O2','O3'):
                target=raw if opt=='raw' else out/(name+'.'+mode+'.'+opt+'.wasm')
                if opt!='raw':p.w.tool('wasm-opt',[raw,'-'+opt,'-o',target])
                item=dict(path=target.name,model=name,mode=mode,opt=opt,recovered=False);manifest['files'].append(item)
                start=time.perf_counter()
                try:
                    program=p.read(target);parse=(time.perf_counter()-start)*1000;samples=[]
                    for _ in range(11):
                        start=time.perf_counter();groups=p.extract(program);samples.append((time.perf_counter()-start)*1000)
                    assert p.signature(groups)==expected,(target,'Incorrect observation signature')
                    tracemalloc.start();p.extract(program);peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
                    recovered=out/(target.stem+'.recovered.wasm');canonical=p.plan(groups,'coalesced');p.compile_wat(p.module(params,canonical),recovered)
                    manifest['files'].append(dict(item,path=recovered.name,recovered=True))
                    analysis.append(dict(path=target.name,status='success',parse_ms=parse,samples_ms=samples,python_peak_bytes=peak,
                                         signature=expected,recovered_stores=len(canonical)))
                except ValueError as e:analysis.append(dict(path=target.name,status='unsupported',reason=str(e)))
        print(json.dumps(dict(generated=name)),flush=True)
    save(out/'manifest.json',manifest);save(out/'analysis.json',analysis);save(out/'transforms.json',transforms)
    checks=json.loads(command(['node',HERE/'check.cjs',out]));save(out/'checks.json',checks)
    print(json.dumps({k:v for k,v in checks.items() if k not in ('records','details')}),flush=True)
    # Separate WABT execution, including prefix state after a trapping call.
    folder=out/'interpreter';folder.mkdir();records=[]
    for item in manifest['files']:
        model=ds[item['model']];wat=p.w.tool('wasm2wat',[out/item['path'],'--fold-exprs','--no-debug-names'])
        # Export invocation of run first, then read memory even after it traps.
        for label,base in [('valid',65480),('partial',65522)]:
            argv=[base]+[0x01020304*i for i in range(1,model['params'])]
            tail='(func (export "check") (result i32) (call 0 '+ ' '.join(f'(i32.const {v})' for v in argv)+'))'
            tail+=''.join(f'(func (export "byte{i}") (result i32) (i32.load8_u (i32.const {65480+i})))' for i in range(56))
            target=folder/(Path(item['path']).stem+'.'+label+'.wasm');p.compile_wat(wat.rstrip()[:-1]+tail+')',target)
            log=p.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf-8')
            memory=bytearray(65536);trap=False
            for offset,width,param in model['stores']:
                address=base+offset
                if address+width>65536:trap=True;break
                memory[address:address+width]=argv[param].to_bytes(4,'little')[:width]
            actual=[int(v) for v in re.findall(r'byte\d+\(\) => i32:(\d+)',log)]
            got_trap='check() => error:' in log
            assert actual==list(memory[65480:]) and got_trap==trap,(item,label,log)
            records.append(dict(path=item['path'],input=label,trap=trap,bytes_checked=56))
    save(out/'interpreter.json',dict(engine='WABT',writer_calls=len(records),memory_reads=len(records)*56,mismatches=0,records=records))
    rng=random.Random(20261018);order=[x for x in manifest['files'] if not x['recovered']]*3;rng.shuffle(order);bench=[]
    for i,item in enumerate(order):bench.append(dict(path=item['path'],process=i,**json.loads(command(['node',HERE/'bench.cjs',out/item['path']]))))
    save(out/'benchmark.json',bench);summary=[]
    for item in manifest['files']:
        if item['recovered']:continue
        rows=[x for x in bench if x['path']==item['path']];medians=[statistics.median(x['samples_ns']) for x in rows]
        summary.append(dict(item,bytes=(out/item['path']).stat().st_size,median_ns=statistics.median(medians),min_ns=min(medians),max_ns=max(medians),
                            public_memory_bytes=rows[0]['public_memory_bytes'],max_rss_kib=max(x['max_rss_kib'] for x in rows)))
    save(out/'summary.json',summary)
    hashes={}
    for src in list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))+[Path(p.w.__file__)]:
        name=src.relative_to(p.w.ROOT).as_posix();hashes[name]=hashlib.sha256(src.read_bytes()).hexdigest();dest=out/'sources'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),node=bench[0]['node'],v8=bench[0]['v8'],cpu=bench[0]['cpu'],
                                   wabt=p.w.tool('wasm-validate',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip(),source_hashes=hashes))
    if args.compare:
        for item in manifest['files']:assert (out/item['path']).read_bytes()==(args.compare/item['path']).read_bytes()
        save(out/'replay.json',dict(identical=len(manifest['files'])))
    print(json.dumps(dict(done=True,binaries=len(manifest['files']),status_counts={s:sum(x['status']==s for x in analysis) for s in set(x['status'] for x in analysis)})),flush=True)


if __name__=='__main__':main()
