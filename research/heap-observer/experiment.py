import argparse,hashlib,json,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
TOOL=ROOT/'.tools/heap-observer-target/release/heap-observer-tool.exe';OPT=ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe';SM=ROOT/'.tools/spidermonkey-150.0.1/js.exe'
FEATURES=['--enable-gc','--enable-reference-types','--enable-multivalue','--enable-extended-const']
def dump(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fixture(name,variant):
    v=variant=='changed';n=42 if v else 41
    if name=='scalar':types='(type $s (struct (field i32 i64 f32 f64)))';init=f'(struct.new $s (i32.const {n}) (i64.const -9223372036854775808) (f32.const -0) (f64.const 1.5))'
    elif name=='packed':types='(type $s (struct (field i8 i16)))';init=f'(struct.new $s (i32.const {256 if v else 255}) (i32.const 65535))'
    elif name=='array':types='(type $s (array i32))';init=f'(array.new $s (i32.const 9) (i32.const {4 if v else 3}))'
    elif name=='deep':types='(type $c (struct (field i32))) (type $s (struct (field (ref $c))))';init=f'(struct.new $s (struct.new $c (i32.const {n})))'
    elif name=='alias':
        types='(type $c (struct (field i32))) (type $s (struct (field (ref $c) (ref $c)))) (global $c (ref $c) (struct.new $c (i32.const 9)))'
        init='(struct.new $s (global.get $c) '+('(struct.new $c (i32.const 9))' if v else '(global.get $c)')+')'
    elif name=='cycle':
        types='(type $s (struct (field (mut (ref null $s))) (field i32)))';init=f'(struct.new $s (ref.null $s) (i32.const {n}))'
    elif name=='recgroup':
        types='(rec (type $s (struct (field (ref null $other)) (field i32))) (type $other (struct (field (ref null $s)))))';init=f'(struct.new $s (ref.null $other) (i32.const {n}))'
    elif name=='subtype':
        types='(type $b (sub (struct (field i32)))) (type $s (sub $b (struct (field i32 i32))))';init=f'(struct.new $s (i32.const 7) (i32.const {n}))'
    elif name=='nan-positive':
        types='(type $s (struct (field f32 f64)))';init=f'(struct.new $s (f32.const nan:0x{2 if v else 1:x}) (f64.const nan:0x{2 if v else 1:x}))'
    else:raise ValueError(name)
    start='(func $init (struct.set $s 0 (global.get $g) (global.get $g))) (start $init)' if name=='cycle' else ''
    return f'(module {types} (global $g (ref $s) {init}) {start} (func (export "get") (result anyref) (global.get $g)))'

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];metadata=[];errors=[];families=['scalar','packed','array','deep','alias','cycle','recgroup','subtype','nan-positive']
    for name in families:
      helper=out/(name+'.observer.wasm');meta_file=out/(name+'.observer.json')
      for variant in ['base','changed']:
        raw=out/(name+'-'+variant+'-O0.wasm');wat=fixture(name,variant);raw.with_suffix('.wat').write_text(wat);raw.write_bytes(wt.wat2wasm(wat))
        if variant=='base':
          t=time.perf_counter_ns();p=subprocess.run([str(TOOL),str(raw),str(helper)],capture_output=True,text=True,timeout=10);meta=json.loads(p.stdout);dump(meta_file,meta)
          metadata.append(dict(name=name,generation_ms=(time.perf_counter_ns()-t)/1e6,**meta))
          if meta['status']!='generated':errors.append(dict(kind='generation',name=name,result=meta));continue
        for level in ['O0','O3-open','O3-closed']:
          path=raw if level=='O0' else out/(name+'-'+variant+'-'+level+'.wasm')
          if level!='O0':
            p=subprocess.run([str(OPT),str(raw),*FEATURES,'-O3',*(['--closed-world'] if level=='O3-closed' else []),'-o',str(path)],capture_output=True,text=True,timeout=15)
            (out/(path.stem+'.opt.stderr')).write_text(p.stderr);p.check_returncode()
          for engine,exe in [('node','node'),('spidermonkey',str(SM))]:
            t=time.perf_counter_ns();p=subprocess.run([exe,str(HERE/'runner.js'),str(path),str(helper),str(meta_file),str(HERE/'observe.js')],capture_output=True,text=True,timeout=5);wall=(time.perf_counter_ns()-t)/1e6
            stem=path.stem+'-'+engine;(out/(stem+'.stdout')).write_text(p.stdout);(out/(stem+'.stderr')).write_text(p.stderr)
            try:r=json.loads(p.stdout)
            except Exception:r=dict(status='process-error',returncode=p.returncode)
            rows.append(dict(name=name,variant=variant,level=level,engine=engine,file=path.name,bytes=path.stat().st_size,wall_ms=wall,result=r))
            if r['status']!='observed':errors.append(dict(kind='run',name=name,variant=variant,level=level,engine=engine,result=r))
    comparisons=[]
    ix={(r['name'],r['variant'],r['level'],r['engine']):r['result'] for r in rows}
    for name in families:
      for en in ['node','spidermonkey']:
        for variant in ['base','changed']:
          base=ix[name,variant,'O0',en]
          for level in ['O3-open','O3-closed']:
            opt=ix[name,variant,level,en];same=base.get('snapshot')==opt.get('snapshot')
            comparisons.append(dict(name=name,variant=variant,engine=en,level=level,snapshot_equal=same,boundary_equal=base.get('boundary')==opt.get('boundary'),contract='comparable' if level=='O3-open' else 'outside-closed-world-contract'))
            if level=='O3-open' and not same:errors.append(dict(kind='open-world-difference',name=name,variant=variant,engine=en))
    faults=[]
    for name in families:
      for level in ['O0','O3-open']:
        for en in ['node','spidermonkey']:
          a,b=ix[name,'base',level,en],ix[name,'changed',level,en];eq=a.get('snapshot')==b.get('snapshot');expected=name=='nan-positive'
          faults.append(dict(name=name,level=level,engine=en,snapshot_equal=eq,boundary_equal=a.get('boundary')==b.get('boundary'),expected_equal=expected))
          if eq!=expected:errors.append(dict(kind='injected-control',name=name,level=level,engine=en))
    report=dict(families=len(families),binaries=len(rows)//2,processes=len(rows),observer_modules=len(metadata),optimization_comparisons=comparisons,fault_controls=faults,helper_bytes=dict(min=min(m['bytes'] for m in metadata),median=statistics.median(m['bytes'] for m in metadata),max=max(m['bytes'] for m in metadata)),errors=errors)
    dump(out/'rows.json',rows);dump(out/'metadata.json',metadata);dump(out/'report.json',report);dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()])
    print(json.dumps(dict(processes=len(rows),errors=errors,open_differences=sum(not c['snapshot_equal'] for c in comparisons if c['level']=='O3-open'),closed_differences=sum(not c['snapshot_equal'] for c in comparisons if c['level']=='O3-closed')),indent=2));assert not errors
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out.resolve())
