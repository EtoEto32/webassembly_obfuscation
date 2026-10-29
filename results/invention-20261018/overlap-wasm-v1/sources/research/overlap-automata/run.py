"""Fresh-output reproduction: Wasm generation, attacks, checks, cost measurements."""
import argparse
from dataclasses import asdict
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
import prototype as p

HERE=Path(__file__).resolve().parent


def save(path,data):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')


def command(args,timeout=180):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=timeout)
    if r.returncode:raise RuntimeError(json.dumps(dict(command=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return r.stdout


def models():
    return dict(suffix010=p.m.pattern([0,1,0]),contains0110=p.m.pattern([0,1,1,0],True),
                mod4=p.m.DFA([[(q+1)%4,(q+2)%4] for q in range(4)],1))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--compare',type=Path);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    ds=models();ds={k:v for k,v in ds.items() if not a.smoke or k=='contains0110'}
    manifest=dict(models={k:asdict(v) for k,v in ds.items()},files=[]);analysis=[];transforms=[]
    for name,d in ds.items():
        src=out/(name+'.plain.raw.wasm');p.s.compile_wat(p.dfa_wat(d),src)
        for mode in ['plain','lift','random','overlap']:
            raw=out/(name+'.'+mode+'.raw.wasm')
            if mode!='plain':transforms.append(dict(model=name,**p.transform(src,raw,mode)))
            for opt in ['raw','O2','O3']:
                target=raw if opt=='raw' else out/(name+'.'+mode+'.'+opt+'.wasm')
                if opt!='raw':p.w.tool('wasm-opt',[raw,'-'+opt,'-o',target])
                item=dict(path=target.name,model=name,mode=mode,opt=opt,recovered=False)
                manifest['files'].append(item)
                try:
                    t=time.perf_counter();program=p.s.read(target);parse=program['parse_validate_ms'];n,template=p.extract(program,out)
                    extract=(time.perf_counter()-t)*1000-parse;attacks=[];chosen=None
                    for method in ['subset','bisimulation','simulation','reverse']:
                        recovered,report=p.attack(n,method)
                        if recovered is not None:
                            equal,pairs=p.m.equivalent(d,recovered);assert equal
                            report.update(equivalent=equal,check_pairs=pairs)
                            report['samples_ms']=[p.attack(n,method)[1]['analysis_ms'] for _ in range(11)]
                            if method=='subset':chosen=recovered
                        attacks.append(report)
                    assert chosen is not None
                    dst=out/(target.stem+'.recovered.wasm');p.s.compile_wat(p.dfa_wat(chosen),dst)
                    manifest['files'].append(dict(item,path=dst.name,recovered=True))
                    analysis.append(dict(path=target.name,status='success',nfa_states=n.n,template=template,parse_validate_ms=parse,
                                         extract_verify_ms=extract,attacks=attacks))
                except ValueError as error:
                    analysis.append(dict(path=target.name,status='unsupported',reason=str(error)))
        print(json.dumps(dict(generated=name)),flush=True)
    save(out/'manifest.json',manifest);save(out/'analysis.json',analysis);save(out/'transforms.json',transforms)
    checks=json.loads(command(['node',HERE/'check.cjs',out]));save(out/'checks.json',checks);print(json.dumps(checks),flush=True)
    # A second engine, with visible data and exported constant-argument wrappers.
    interp=[];idata=bytes([0,1,2,3,254,255,128,127]);folder=out/'interpreter';folder.mkdir()
    for item in manifest['files']:
        wat=p.w.tool('wasm2wat',[out/item['path'],'--fold-exprs','--no-debug-names'])
        tail='(data (i32.const 0) "'+''.join('\\%02x'%b for b in idata)+'")'
        for i,length in enumerate([0,1,3,8]):tail+=f'(func (export "check{i}") (result i32) (call 0 (i32.const 0) (i32.const {length})))'
        binary=folder/item['path'];p.s.compile_wat(wat.rstrip()[:-1]+tail+')',binary)
        log=p.w.tool('wasm-interp',[binary,'--run-all-exports']);binary.with_suffix('.log').write_text(log,encoding='utf-8')
        got=[int(x) for x in re.findall(r'check\d+\(\) => i32:(\d+)',log)]
        expected=[ds[item['model']].accepts([x&1 for x in idata[:n]]) for n in [0,1,3,8]]
        assert got==expected,(item,got,expected);interp.append(dict(path=item['path'],got=got,expected=expected))
    save(out/'interpreter.json',dict(calls=len(interp)*4,mismatches=0,records=interp))
    # Valid Wasm outside the certified template must be rejected.
    negatives=[];base=out/(next(iter(ds))+'.overlap.raw.wasm')
    wat=p.w.tool('wasm2wat',[base,'--fold-exprs','--no-debug-names'])
    for kind,changed in [('different_address',wat.replace('(i32.add','(i32.sub',1)),
                         ('extra_memory_write',wat.replace('(local.set 4','(i32.store8 (i32.const 0) (i32.const 7)) (local.set 4',1)),
                         ('different_bit_test',wat.replace('(i64.ne','(i64.eq',1))]:
        target=out/('negative-'+kind+'.wasm');p.s.compile_wat(changed,target)
        try:p.extract(p.s.read(target),out);raise AssertionError('Unsound acceptance: '+kind)
        except (ValueError,IndexError,TypeError) as error:negatives.append(dict(kind=kind,status='rejected',reason=str(error)))
    save(out/'negatives.json',negatives)
    order=[x for x in manifest['files'] if not x['recovered']]*3;random.Random(20261018).shuffle(order);bench=[]
    for i,item in enumerate(order):
        result=json.loads(command(['node',HERE/'bench.cjs',out/item['path']]));bench.append(dict(path=item['path'],process=i,**result))
    save(out/'benchmark.json',bench)
    table=[]
    for item in manifest['files']:
        if item['recovered']:continue
        rows=[r for r in bench if r['path']==item['path']];samples=[statistics.median(r['samples_ns']) for r in rows]
        table.append(dict(item,bytes=(out/item['path']).stat().st_size,median_ns=statistics.median(samples),min_ns=min(samples),max_ns=max(samples),
                          max_rss_kib=max(r['max_rss_kib'] for r in rows),public_memory_bytes=rows[0]['public_memory_bytes']))
    save(out/'summary.json',table)
    snapshots=out/'sources';snapshots.mkdir();hashes={}
    sources=list(HERE.glob('*.py'))+list(HERE.glob('*.cjs'))+[Path(p.s.__file__),Path(p.w.__file__)]
    for src in sources:
        relative=str(src.relative_to(p.w.ROOT)).replace('\\','/');hashes[relative]=hashlib.sha256(src.read_bytes()).hexdigest()
        dest=snapshots/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),node=bench[0]['node'],v8=bench[0]['v8'],
                                   cpu=bench[0]['cpu'],wabt=p.w.tool('wasm-validate',['--version']).strip(),
                                   binaryen=p.w.tool('wasm-opt',['--version']).strip(),source_hashes=hashes))
    if a.compare:
        comparisons=[]
        for item in manifest['files']:
            path=item['path'];equal=(out/path).read_bytes()==(a.compare/path).read_bytes();assert equal
            comparisons.append(dict(path=path,identical=equal))
        save(out/'replay.json',dict(identical=len(comparisons),records=comparisons))
    print(json.dumps(dict(done=True,output=str(out),binaries=len(manifest['files']),recoveries=sum(x['status']=='success' for x in analysis))),flush=True)


if __name__=='__main__':main()
