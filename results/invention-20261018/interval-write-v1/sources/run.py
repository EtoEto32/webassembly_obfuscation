"""Reproduce a bounded candidate gate, including adaptive recovery and cost controls."""
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
import prototype as p

HERE=Path(__file__).resolve().parent


def save(path,obj):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')


def anf(t):
    if t[0]=='lt':return {frozenset([t])}
    if t[0]=='const':return {frozenset()} if t[1] else set()
    a,b=anf(t[1]),anf(t[2])
    if t[0]=='xor':return a^b
    product=set()
    for u in a:
        for v in b:product.symmetric_difference_update({u|v})
    return product if t[0]=='and' else a^b^product


def models():
    leaves=[('lt',i,7) for i in range(7)]
    fan=leaves[0]
    for x in leaves[1:]:fan=('xor',fan,x)
    return {'pair2':dict(n=2,tree=('lt',0,1)),
            'range4':dict(n=4,tree=('and',('lt',0,1),('lt',2,3))),
            'fanout8':dict(n=8,tree=fan),
            'mixed8':dict(n=8,tree=('or',('and',('lt',0,1),('lt',2,3)),
                                      ('and',('xor',('lt',4,5),('lt',6,5)),('lt',2,7))))}


def ref(t,args):
    if t[0]=='lt':return int((args[t[1]]&255)<(args[t[2]]&255))
    if t[0]=='const':return t[1]
    a,b=ref(t[1],args),ref(t[2],args)
    return a&b if t[0]=='and' else a|b if t[0]=='or' else a^b


def nodes(x):
    if not isinstance(x,list):return
    yield x
    for child in x[1:]:yield from nodes(child)


def command(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180)
    if r.returncode:raise RuntimeError(json.dumps(dict(command=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return r.stdout


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path);args=ap.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    data=models();files=[];transforms=[];analysis=[]
    for name,model in data.items():
        src=out/(name+'.plain.raw.wasm');p.compile_wat(p.module(model['n'],p.original(model['tree'])),src)
        for mode in ['plain','table','individual','shared']:
            raw=out/(name+'.'+mode+'.raw.wasm')
            if mode!='plain':transforms.append(dict(model=name,**p.transform(src,raw,mode)))
            for opt in ['raw','O2','O3']:
                target=raw if opt=='raw' else out/(name+'.'+mode+'.'+opt+'.wasm')
                if opt!='raw':p.w.tool('wasm-opt',[raw,'-'+opt,'--enable-multimemory','--enable-bulk-memory','-o',target])
                m,parse=p.load(target)
                try:
                    report=p.recover(m)
                    samples=[p.recover(m)['analysis_ms'] for _ in range(9)]
                    assert anf(report['tree'])==anf(model['tree'])
                except Exception as e:
                    save(out/'analysis-failure.json',dict(path=target.name,kind=type(e).__name__,reason=str(e)))
                    raise
                record=dict(path=target.name,model=name,mode=mode,opt=opt,recovered=False)
                files.append(record)
                analysis.append(dict(path=target.name,status='success',parse_validate_ms=parse,
                                     samples_ms=samples,report=report,boolean_identity=True))
                recovered=out/(target.stem+'.recovered.wasm')
                p.compile_wat(p.module(model['n'],p.original(report['tree'])),recovered)
                files.append(dict(record,path=recovered.name,recovered=True))
        print(json.dumps(dict(generated=name)),flush=True)

    negative=[];rejections=[]
    for kind in ['long_fill','missing_reset']:
        m,_=p.load(out/'pair2.shared.raw.wasm')
        f=next(x for x in m[1:] if x[0]=='func')
        if kind=='long_fill':
            fill=next(x for x in f[1:] if isinstance(x,list) and x[0]=='memory.fill' and x[3]==p.c(1))
            fill[4]=['i32.add',fill[4],p.c(1)]
        else:
            reset=next(x for x in f[1:] if isinstance(x,list) and x[0]=='memory.fill' and x[3]==p.c(0))
            f.remove(reset)
        target=out/(kind+'.wasm');p.compile_wat(p.w.emit(m),target)
        try:p.recover(p.load(target)[0])
        except ValueError as e:rejections.append(dict(kind=kind,rejected=True,reason=str(e)))
        else:raise AssertionError('Unsound recovery accepted '+kind)
        negative.append(dict(kind=kind,path=target.name))
    # An extra public-memory write is not accepted by the source transformer.
    m,_=p.load(out/'pair2.plain.raw.wasm');f=next(x for x in m[1:] if x[0]=='func')
    f.insert(len(f)-1,['i32.store8',p.c(0),p.c(1)])
    target=out/'source-effect.wasm';p.compile_wat(p.w.emit(m),target)
    try:p.transform(target,out/'must-not-exist.wasm','shared')
    except ValueError as e:rejections.append(dict(kind='source_effect',rejected=True,reason=str(e)))
    else:raise AssertionError('Source effects accepted')
    assert not (out/'must-not-exist.wasm').exists()

    manifest=dict(models=data,files=files,negative=negative)
    save(out/'manifest.json',manifest);save(out/'transforms.json',transforms)
    save(out/'analysis.json',analysis);save(out/'negative-analysis.json',rejections)
    stdout=command(['node',HERE/'check.cjs',out]);(out/'node-check.log').write_text(stdout,encoding='utf-8');print(stdout.strip(),flush=True)

    interpreter=[];folder=out/'interpreter';folder.mkdir()
    for item in files:
        m,_=p.load(out/item['path']);n=data[item['model']]['n'];expected=[]
        cases=[[0]*n,[255]*n,list(range(n)),[0xffffffff if i%2 else 128 for i in range(n)]]
        for i,a in enumerate(cases):
            m.append(['func',['export','"test'+str(i)+'"'],['result','i32'],['call','0',*[p.c(x if x<2**31 else x-2**32) for x in a]]])
            expected.append(ref(data[item['model']]['tree'],a))
        target=folder/Path(item['path']).name;p.compile_wat(p.w.emit(m),target)
        log=p.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf-8')
        got=[int(v) for v in re.findall(r'test\d+\(\) => i32:(\d+)',log)]
        assert got==expected,(item,got,expected)
        interpreter.append(dict(path=item['path'],got=got,expected=expected))
    save(out/'interpreter.json',dict(calls=len(interpreter)*4,mismatches=0,records=interpreter))

    schedule=[(item,i) for item in files if not item['recovered'] for i in range(3)]
    random.Random(20261018).shuffle(schedule);timings=[]
    for j,(item,i) in enumerate(schedule):
        v=json.loads(command(['node',HERE/'bench.cjs',out/item['path'],data[item['model']]['n']]))
        timings.append(dict(path=item['path'],trial=i,**v))
        if (j+1)%24==0:print(json.dumps(dict(measured=j+1,total=len(schedule))),flush=True)
    save(out/'timings.json',dict(fresh_processes=len(schedule),records=timings))
    rows=[]
    for item in files:
        if item['recovered']:continue
        runs=[r for r in timings if r['path']==item['path']]
        meds=[statistics.median(r['samples_ns']) for r in runs]
        a=next(r for r in analysis if r['path']==item['path'])
        rows.append(dict(**item,bytes=(out/item['path']).stat().st_size,median_ns=statistics.median(meds),
                         min_process_ns=min(meds),max_process_ns=max(meds),analysis_ms=statistics.median(a['samples_ms']),
                         parse_validate_ms=a['parse_validate_ms'],private_bytes=0 if item['mode']=='plain' else 65536,
                         max_rss_kib=[r['max_rss_kib'] for r in runs]))
    save(out/'summary.json',rows)
    table='# O3実測比較\n\nns/callは各process中央値の中央値、括弧内は3processの範囲。\n\n|例|方式|bytes|ns/call|解析ms|\n|---|---|---:|---:|---:|\n'
    for r in rows:
        if r['opt']=='O3':table+=f"|{r['model']}|{r['mode']}|{r['bytes']}|{r['median_ns']:.2f} ({r['min_process_ns']:.2f}–{r['max_process_ns']:.2f})|{r['analysis_ms']:.4f}|\n"
    (out/'comparison.md').write_text(table,encoding='utf-8')
    snap=out/'sources';snap.mkdir()
    for name in ['prototype.py','run.py','check.cjs','bench.cjs','plan.md']:shutil.copy2(HERE/name,snap/name)
    shutil.copy2(p.w.__file__,snap/'common-prototype.py')
    hashes={r['path']:hashlib.sha256((out/r['path']).read_bytes()).hexdigest() for r in files}
    save(out/'binary-sha256.json',hashes)
    audit=dict(main_conditions=len(analysis),recovered_binaries=len(analysis),
               status_counts=dict(success=len(analysis),unsupported=0,crash=0,timeout=0,analysis_failure=0),
               source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in snap.iterdir()})
    if args.compare:
        old=json.loads((args.compare/'binary-sha256.json').read_text())
        audit['comparison']=dict(equal=old==hashes,binaries=len(hashes))
        assert old==hashes
    save(out/'audit.json',audit)
    save(out/'environment.json',dict(python=platform.python_version(),platform=platform.platform(),
         node=timings[0]['node'],v8=timings[0]['v8'],cpu=timings[0]['cpu'],
         wabt=p.w.tool('wasm2wat',['--version']).strip(),binaryen=p.w.tool('wasm-opt',['--version']).strip()))
    print(json.dumps(audit),flush=True)


if __name__=='__main__':main()
