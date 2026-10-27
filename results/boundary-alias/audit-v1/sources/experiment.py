"""Generate bounded GC boundary fixtures, optimize, and compare actual JS engines."""
import argparse,collections,hashlib,json,platform,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
OPT=ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe'
FEATURES=['--enable-gc','--enable-reference-types','--enable-multivalue','--enable-extended-const']
SM=ROOT/'.tools/spidermonkey-150.0.1/js.exe'
PRINTER=ROOT/'results/type-context/priors-v2/fuzz_shell.js'
FAMILIES=['fresh','alternating','retained-input','callback','replace','trap-after-log','null-mixed']
def dump(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def module(kind,family,variant):
    typ='(struct (field (mut i32)))' if kind=='struct' else '(array (mut i32))'
    new='(struct.new $t (i32.const 7))' if kind=='struct' else '(array.new $t (i32.const 7) (i32.const 2))'
    a='(global.get $a)';b='(global.get $b)';fault=variant=='fault'
    choose='(if (result eqref) (i32.and (local.get $i) (i32.const 1)) (then '+a+') (else '+b+'))'
    prefix=''
    if family=='fresh':body=a if fault else new
    elif family=='alternating':body=a if fault else choose
    elif family=='retained-input':body=new if fault else '(local.get $x)'
    elif family=='callback':
        prefix='(call $log '+(a if fault else choose)+')';body='(ref.null eq)'
    elif family=='replace':
        prefix='' if fault else '(if (i32.eq (local.get $i) (i32.const 3)) (then (global.set $a '+new+')))'
        body=a
    elif family=='trap-after-log':
        prefix='(call $log '+(a if fault else choose)+') (if (i32.eq (local.get $i) (i32.const 3)) (then unreachable))'
        body='(ref.null eq)'
    elif family=='null-mixed':body='(if (result eqref) (i32.and (local.get $i) (i32.const 1)) (then (ref.null eq)) (else '+(a if fault else new)+'))'
    else:raise ValueError(family)
    # Unobserved allocations are intentionally not assigned observable IDs.
    private=('(drop '+new+') (drop '+new+')') if variant=='private' else ''
    return '\n'.join(['(module',' (type $t '+typ+')',' (import "env" "log" (func $log (param eqref)))',
        ' (global $a (mut (ref $t)) '+new+')',' (global $b (ref $t) '+new+')',
        ' (func (export "seed") (result eqref) '+new+')',
        ' (func (export "step") (param $i i32) (param $x eqref) (result eqref)',private,prefix,body,')',')'])

def main(out):
    out.mkdir(parents=True,exist_ok=False);start=time.perf_counter_ns();cfg=wt.Config();engine=wt.Engine(cfg);rows=[];files=[]
    for kind in ['struct','array']:
      for family in FAMILIES:
       for variant in ['base','fault','private']:
        name='%s-%s-%s'%(kind,family,variant);wat=out/(name+'.wat');raw=out/(name+'-O0.wasm');t=time.perf_counter_ns()
        wat.write_text(module(kind,family,variant),encoding='utf8');raw.write_bytes(wt.wat2wasm(wat.read_text()));gen_ms=(time.perf_counter_ns()-t)/1e6
        for level in ['O0','O2','O3']:
          path=out/(name+'-'+level+'.wasm');elapsed=0
          if level!='O0':
            t=time.perf_counter_ns();p=subprocess.run([str(OPT),str(raw),*FEATURES,'-'+level,'-o',str(path)],capture_output=True,text=True,timeout=20);elapsed=(time.perf_counter_ns()-t)/1e6
            (out/(name+'-'+level+'.stderr')).write_text(p.stderr,encoding='utf8')
            if p.returncode:raise RuntimeError(p.stderr)
          wt.Module(engine,path.read_bytes())
          rows.append(dict(name=name,kind=kind,family=family,variant=variant,level=level,file=path.name,bytes=path.stat().st_size,sha256=sha(path),generation_ms=gen_ms,optimization_ms=elapsed,validation='passed'))
    dump(out/'cases.json',rows)
    source=PRINTER.read_text(encoding='utf8');lo=source.index('function printed(');hi=source.index('// Fuzzer integration.',lo)
    # Keep the upstream function verbatim. It is a renderer baseline, not a
    # claim that all Binaryen fuzzing oracles are reproduced here.
    (out/'upstream-printed.js').write_text('function assert(x){if(!x)throw new Error("assertion");}\n'+source[lo:hi],encoding='utf8')
    reports=[]
    for name,command in [('node',['node',str(HERE/'runner.js'),str(out)]),('spidermonkey',[str(SM),str(HERE/'runner.js'),str(out)])]:
        t=time.perf_counter_ns();p=subprocess.run(command,capture_output=True,text=True,timeout=60);elapsed=(time.perf_counter_ns()-t)/1e6
        (out/(name+'.stdout')).write_text(p.stdout,encoding='utf8');(out/(name+'.stderr')).write_text(p.stderr,encoding='utf8')
        if p.returncode:raise RuntimeError(name+': '+p.stderr+' '+p.stdout[:1000])
        report=json.loads(p.stdout);dump(out/(name+'.json'),report);reports.append(dict(engine=name,process_wall_ms=elapsed,summary=report['summary']))
    n=json.loads((out/'node.json').read_text());s=json.loads((out/'spidermonkey.json').read_text())
    cross=[]
    for a,b in zip(n['rows'],s['rows']):
        for key in ['file','trace','tokens','printed','calls','events','direct_agrees']:
            if a[key]!=b[key]:cross.append(dict(file=a['file'],key=key))
    report=dict(platform=platform.platform(),python=sys.version,binaries=len(rows),total_bytes=sum(r['bytes'] for r in rows),source_modules=len(rows)//3,engines=reports,cross_engine_differences=cross,upstream_printer_sha256=sha(PRINTER),optimizer_sha256=sha(OPT),median_generation_ms=statistics.median(r['generation_ms'] for r in rows),median_optimization_ms={l:statistics.median(r['optimization_ms'] for r in rows if r['level']==l) for l in ['O2','O3']},experiment_wall_ms=(time.perf_counter_ns()-start)/1e6)
    dump(out/'report.json',report)
    dump(out/'manifest.json',[dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()])
    print(json.dumps(report,indent=2));assert not cross

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out.resolve())
