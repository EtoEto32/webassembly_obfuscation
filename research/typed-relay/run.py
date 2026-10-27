"""Run the typed-relay counterexample gate in a fresh directory."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import random
import re
import statistics
import subprocess
import prototype as p

HERE=Path(__file__).resolve().parent
MODES=['plain','ref','tail1','tail4','tail8','call4']


def save(path,x):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')


def command(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180)
    if r.returncode:raise RuntimeError(json.dumps(dict(args=list(map(str,args)),stdout=r.stdout,stderr=r.stderr)))
    return r.stdout


def kernel(name):
    updates={
        'rolling':'''(local.set 4 (i32.add (i32.mul (i32.xor (i32.rotl (local.get 4) (i32.const 5)) (local.get 6)) (i32.const 33)) (local.get 3)))''',
        'dual':'''(local.set 4 (i32.add (local.get 4) (i32.mul (local.get 6) (i32.add (local.get 3) (i32.const 1)))))
                  (local.set 5 (i32.xor (i32.rotr (local.get 5) (i32.const 3)) (i32.sub (local.get 4) (local.get 6))))''',
        'update':'''(local.set 4 (i32.add (i32.rotl (local.get 4) (i32.const 7)) (local.get 6)))
                    (if (i32.and (local.get 6) (i32.const 1)) (then
                      (i32.store8 (i32.add (local.get 0) (local.get 3)) (i32.xor (local.get 6) (local.get 4)))))
                    (local.set 5 (i32.xor (local.get 5) (i32.mul (local.get 4) (i32.const 17))))'''
    }
    return '''(module (memory (export "memory") 1 1)
      (func (export "run") (param i32 i32 i32) (result i32) (local i32 i32 i32 i32)
        (local.set 4 (local.get 2))
        (local.set 5 (i32.xor (local.get 2) (i32.const 19088743)))
        (block $exit (loop $loop
          (br_if $exit (i32.ge_u (local.get 3) (local.get 1)))
          (local.set 6 (i32.load8_u (i32.add (local.get 0) (local.get 3))))
          '''+updates[name]+'''
          (local.set 3 (i32.add (local.get 3) (i32.const 1)))
          (br $loop)))
        (i32.xor (local.get 4) (local.get 5))))'''


def zero_reference(model,n,seed):
    mask=0xffffffff;a=seed&mask;b=a^19088743
    for i in range(n):
        if model=='rolling':a=((((a<<5)|(a>>27))&mask)*33+i)&mask
        elif model=='dual':b=((b>>3)|(b<<29))&mask;b^=a
        else:a=((a<<7)|(a>>25))&mask;b^=(a*17)&mask
    return (a^b)&mask


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--compare',type=Path)
    ap.add_argument('--smoke',action='store_true');a=ap.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    models=['rolling'] if a.smoke else ['rolling','dual','update']
    files=[];analysis=[];transforms=[];flows=[]
    for model in models:
        src=out/(model+'.plain.raw.wasm');p.compile_wat(kernel(model),src)
        for mode in MODES:
            raw=out/(model+'.'+mode+'.raw.wasm')
            if mode!='plain':transforms.append(dict(model=model,**p.transform(src,raw,mode)))
            for opt in ['raw','O2','O3']:
                target=raw if opt=='raw' else out/(model+'.'+mode+'.'+opt+'.wasm')
                if opt!='raw':p.w.tool('wasm-opt',[raw,'-'+opt,'--enable-reference-types','--enable-gc','--enable-tail-call','-o',target])
                m,parse=p.load(target);rec=dict(path=target.name,model=model,mode=mode,opt=opt,recovered=False)
                files.append(rec)
                flows.extend(dict(path=target.name,**p.reference_flow(m,k)) for k in [0,1,2,4,8])
                try:
                    r=p.recover(m);samples=[p.recover(m)['analysis_ms'] for _ in range(11)]
                    recovered=out/(target.stem+'.recovered.wasm');p.compile_wat(p.w.emit(r.pop('module')),recovered)
                    files.append(dict(rec,path=recovered.name,recovered=True))
                    counts={op:sum(x[0]==op for x in p.nodes(m)) for op in ('call','return_call','call_ref','return_call_ref')}
                    analysis.append(dict(path=target.name,status='success',parse_validate_ms=parse,samples_ms=samples,
                                         summary=r,instruction_counts=counts,functions=sum(x[0]=='func' for x in m[1:])))
                except ValueError as e:
                    analysis.append(dict(path=target.name,status='unsupported',reason=str(e)))
        print(json.dumps(dict(generated=model)),flush=True)
    save(out/'files.json',files);save(out/'analysis.json',analysis);save(out/'transforms.json',transforms);save(out/'reference-flow.json',flows)
    # Rejection tests: an operation with reordered arguments cannot be naively
    # substituted when source operands may trap or store. An added store is impure.
    negatives=[]
    for kind in ['reordered','side_effect','cycle']:
        m,_=p.load(out/(models[0]+'.tail4.raw.wasm'));fs=[x for x in m[1:] if x[0]=='func']
        if kind=='reordered':
            leaf=fs[1];expr=p.body(leaf)[0];expr[1],expr[2]=expr[2],expr[1]
        elif kind=='side_effect':
            fs[1].insert(-1,['i32.store8',['i32.const','0'],['i32.const','9']])
        else:
            # The top relay calls itself: valid Wasm, but not a proved finite summary.
            p.body(fs[-1])[0][1]=str(len(fs)-1)
        path=out/('negative-'+kind+'.wasm');p.compile_wat(p.w.emit(m),path)
        parsed,_=p.load(path)
        try:p.recover(parsed);status='unexpected_accept';reason=''
        except ValueError as e:status='rejected';reason=str(e)
        negatives.append(dict(kind=kind,status=status,reason=reason))
        assert status=='rejected'
    save(out/'negative.json',negatives)
    check=json.loads(command(['node',HERE/'check.cjs',out, '100' if a.smoke else '1000']))
    save(out/'correctness.json',check)
    assert check['mismatches']==0
    benches=[];rng=random.Random(20261018);ordered=[x for x in files if not x['recovered']]
    for session in range(1 if a.smoke else 3):
        rng.shuffle(ordered)
        for f in ordered:
            b=json.loads(command(['node',HERE/'bench.cjs',out/f['path']]))
            benches.append(dict(path=f['path'],session=session,**b))
        print(json.dumps(dict(bench_session=session)),flush=True)
    save(out/'performance.json',benches)
    # Independent interpreter checks with deterministic zero-initialized memory.
    wabt=[]
    for f in files:
        args=[str(p.w.WABT/'wasm-interp.exe'),str(out/f['path']),*p.FLAGS,'--run-export=run','--argument=i32:0','--argument=i32:16','--argument=i32:1']
        try:
            r=subprocess.run(args,capture_output=True,text=True,timeout=2)
            wabt.append(dict(path=f['path'],status='success' if r.returncode==0 else 'tool_error',exit_code=r.returncode,output=r.stdout.strip(),stderr=r.stderr))
        except subprocess.TimeoutExpired:
            wabt.append(dict(path=f['path'],status='timeout',timeout_seconds=2))
    for model in models:
        baseline=next(x['output'] for x in wabt if x['path']==model+'.plain.raw.wasm' and x['status']=='success')
        for x in wabt:
            if x['path'].startswith(model+'.') and x['status']=='success':
                x['baseline_output']=baseline
                if x['output']!=baseline:x['status']='value_mismatch'
    save(out/'wabt.json',wabt)
    binaryen=[]
    for f in files:
        module,_=p.load(out/f['path'])
        cases=[(0,0,1),(0,16,1),(65535,1,-1)]
        script=p.w.emit(module)+'\n'+'\n'.join(
            '(assert_return (invoke "run" (i32.const %d) (i32.const %d) (i32.const %d)) (i32.const %d))'%(
                addr,n,seed,zero_reference(f['model'],n,seed)) for addr,n,seed in cases)
        script+='\n(assert_trap (invoke "run" (i32.const 65535) (i32.const 2) (i32.const 1)) "out of bounds memory access")\n'
        path=out/(Path(f['path']).stem+'.wast');path.write_text(script,encoding='utf-8')
        r=subprocess.run([str(p.w.BINARYEN/'wasm-shell.exe'),str(path)],capture_output=True,text=True,timeout=5)
        binaryen.append(dict(path=f['path'],calls=4,status='success' if r.returncode==0 else 'tool_error',exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
    save(out/'binaryen-interpreter.json',binaryen)
    assert all(x['status']=='success' for x in binaryen)
    snapshots={}
    for path in sorted(HERE.glob('*')):
        if path.suffix in ('.py','.cjs','.md'):snapshots[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    hashes={f['path']:hashlib.sha256((out/f['path']).read_bytes()).hexdigest() for f in files}
    replay=None
    if a.compare:
        before=json.loads((a.compare/'manifest.json').read_text(encoding='utf-8'))['binaries']
        replay=dict(compare=str(a.compare),same_binaries=hashes==before);assert hashes==before
    manifest=dict(python=platform.python_version(),platform=platform.platform(),binaries=hashes,sources=snapshots,
                  tools={name:p.w.tool(name,['--version']).strip() for name in ('wat2wasm','wasm-opt')},replay=replay)
    save(out/'manifest.json',manifest)
    lines=['# Typed relay measurements','','Timings are medians; analysis excludes WABT parse/validation. Runtime includes the JS call loop.',
           '','|model|mode|opt|bytes|runtime ns/call|analysis ms|helpers|calls/ref/tail|','|---|---|---|---:|---:|---:|---:|---|']
    for f in files:
        if f['recovered']:continue
        perf=[b for b in benches if b['path']==f['path']];an=next(x for x in analysis if x['path']==f['path'])
        ns=statistics.median(statistics.median(x['samples_ns']) for x in perf)
        ms=statistics.median(an['samples_ms']) if an['status']=='success' else None
        lines.append('|'+ '|'.join(map(str,[f['model'],f['mode'],f['opt'],(out/f['path']).stat().st_size,round(ns,2),
                                            round(ms,6) if ms is not None else an['status'],an.get('summary',{}).get('helper_summaries'),an.get('instruction_counts')]))+'|')
    (out/'comparison.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(done=True,files=len(files),calls=check['calls'],analysis={s:sum(x['status']==s for x in analysis) for s in ('success','unsupported')})),flush=True)


if __name__=='__main__':main()
