"""Measure observable GC alias events in unmodified Binaryen-generated guests.

Uses the actual upstream shell, inserting only an extra boundary renderer.
No new guest exports or instrumentation. Bounded local fresh processes.
"""
import argparse,collections,hashlib,json,random,subprocess,time
from pathlib import Path
from experiment import ROOT,HERE,OPT,SM,PRINTER,FEATURES,wt,dump,sha

HOOK=r'''
var __aliasIds = new WeakMap(), __aliasNext = 0, __aliasTrace = [];
var __aliasClassifier = new WebAssembly.Instance(new WebAssembly.Module(readBinary(argv[0].replace(/[^\\/]+$/, 'classifier.wasm')))).exports.isGC;
var __aliasOriginalPrinted = printed;
printed = function(x, y) {
  if (x !== null && typeof x === 'object' && __aliasClassifier(x)) {
    if (!__aliasIds.has(x)) __aliasIds.set(x, __aliasNext++);
    __aliasTrace.push(__aliasIds.get(x));
  }
  return __aliasOriginalPrinted(x, y);
};
'''
TAIL="\nconsole.log('[boundary-alias] ' + JSON.stringify({events:__aliasTrace.length,distinct:__aliasNext,trace:__aliasTrace}));\n"

def run(cmd,seconds):
    t=time.perf_counter_ns()
    try:
        p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=seconds)
        return dict(status='completed' if p.returncode==0 else 'process-error',code=p.returncode,stdout=p.stdout,stderr=p.stderr,wall_ms=(time.perf_counter_ns()-t)/1e6)
    except subprocess.TimeoutExpired as e:
        def txt(x):return x.decode('utf8','replace') if isinstance(x,bytes) else x or ''
        return dict(status='timeout',stdout=txt(e.stdout),stderr=txt(e.stderr),wall_ms=(time.perf_counter_ns()-t)/1e6)

def main(out,seeds):
    out.mkdir(parents=True,exist_ok=False);source=PRINTER.read_text(encoding='utf8');marker='// Build the main wasm.';assert source.count(marker)==1
    classifier='(module (func (export "isGC") (param externref) (result i32) (i32.or (ref.test (ref struct) (any.convert_extern (local.get 0))) (ref.test (ref array) (any.convert_extern (local.get 0))))))'
    (out/'classifier.wat').write_text(classifier);(out/'classifier.wasm').write_bytes(wt.wat2wasm(classifier))
    shell=out/'alias-fuzz-shell.js';shell.write_text(source.replace(marker,HOOK+'\n'+marker)+TAIL,encoding='utf8')
    rows=[];generations=[];cfg=wt.Config();engine=wt.Engine(cfg)
    for seed in range(seeds):
        rng=random.Random(202610270000+seed);inp=out/('%d.seed'%seed);inp.write_bytes(bytes(rng.getrandbits(8) for _ in range(1024)))
        raw=out/('%d-O0.wasm'%seed);cmd=[OPT,inp,'-ttf','--no-fuzz-memory','--no-fuzz-oob',*FEATURES,'-o',raw];g=run(cmd,10)
        generation=dict(seed=seed,status=g['status'],wall_ms=g['wall_ms'],command=list(map(str,cmd)),stderr=g['stderr']);generations.append(generation)
        if g['status']!='completed':continue
        for level in ['O0','O3']:
            wasm=out/('%d-%s.wasm'%(seed,level));o=None
            if level=='O3':
                o=run([OPT,raw,*FEATURES,'-O3','-o',wasm],10)
                if o['status']!='completed':rows.append(dict(seed=seed,level=level,engine='optimizer',**o));continue
            try:wt.Module(engine,wasm.read_bytes());valid='passed'
            except Exception as e:valid=str(e)
            for en,exe in [('node','node'),('spidermonkey',SM)]:
                r=run([exe,shell,wasm],3);prefix='%d-%s-%s'%(seed,level,en)
                (out/(prefix+'.stdout')).write_text(r.pop('stdout'),encoding='utf8');(out/(prefix+'.stderr')).write_text(r.pop('stderr'),encoding='utf8')
                output=(out/(prefix+'.stdout')).read_text(encoding='utf8');line=next((x for x in output.splitlines() if x.startswith('[boundary-alias] ')),None)
                alias=json.loads(line[len('[boundary-alias] '):]) if line else None
                rows.append(dict(seed=seed,level=level,engine=en,file=wasm.name,sha256=sha(wasm),bytes=wasm.stat().st_size,validation=valid,alias=alias,optimization_ms=o['wall_ms'] if o else 0,stdout_file=prefix+'.stdout',stderr_file=prefix+'.stderr',**r))
        if seed%16==0:print(json.dumps(dict(seed=seed,rows=len(rows))),flush=True)
    report=dict(seeds=seeds,generation_status=dict(collections.Counter(g['status'] for g in generations)),execution_status={},comparisons=[],upstream_source_sha256=sha(PRINTER),guest_mutation='none',generator_options=['-ttf','--no-fuzz-memory','--no-fuzz-oob',*FEATURES])
    for en in ['node','spidermonkey']:
        rs=[r for r in rows if r['engine']==en];report['execution_status'][en]=dict(collections.Counter(r['status'] for r in rs))
        for seed in range(seeds):
            pair=[r for r in rs if r['seed']==seed]
            if len(pair)==2 and all(r['alias'] is not None for r in pair):
                report['comparisons'].append(dict(engine=en,seed=seed,equal=pair[0]['alias']==pair[1]['alias'],events=pair[0]['alias']['events'],distinct=pair[0]['alias']['distinct']))
    cs=report['comparisons'];report['summary']=dict(pairs=len(cs),nonempty_pairs=sum(c['events']>0 for c in cs),repeated_identity_pairs=sum(c['events']>c['distinct'] for c in cs),differences=sum(not c['equal'] for c in cs))
    dump(out/'rows.json',rows);dump(out/'generation.json',generations);dump(out/'report.json',report)
    dump(out/'manifest.json',[dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()]);print(json.dumps({k:v for k,v in report.items() if k!='comparisons'},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--seeds',type=int,default=64);a=ap.parse_args();main(a.out.resolve(),a.seeds)
