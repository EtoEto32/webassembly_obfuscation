"""Factorial comparison of two minimal harness repairs, on fixed real binaries."""
import argparse,collections,importlib.util,json,shutil,statistics,subprocess,time
from pathlib import Path
from experiment import ROOT,HERE,SM,PRINTER,wt,dump,sha
spec=importlib.util.spec_from_file_location('alias_real_generator',HERE/'real-generator.py')
real_generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(real_generator);run=real_generator.run
INTERFACE=ROOT/'.tools/boundary-alias-interface-target/release/boundary-alias-interface.exe'
SOURCE=ROOT/'results/boundary-alias/binaryen-v2'

def make_shells(out):
    source=PRINTER.read_text(encoding='utf8');hook=(HERE/'caller-hook.js').read_text(encoding='utf8')
    assert source.count('// Build the main wasm.')==1 and source.count('rawExports[key] = value;')==1
    tail="\nconsole.log('[caller-study] '+JSON.stringify({caller:__callerMode,observer:__observerMode,calls:__calls,events:__trace.length,distinct:__next,trace:__trace,multi_slots:__multiSlots}));\n"
    paths={}
    for caller in ['null','typed']:
      for observer in ['flat','multi']:
        body=hook.replace('__CALLER__',caller).replace('__OBSERVER__',observer)
        text=source.replace('rawExports[key] = value;','rawExports[key] = value; __registerExport(key, value);').replace('// Build the main wasm.',body+'\n// Build the main wasm.')+tail
        p=out/('%s-%s-shell.js'%(caller,observer));p.write_text(text,encoding='utf8');paths[caller,observer]=p
    shutil.copy2(SOURCE/'classifier.wasm',out/'classifier.wasm')
    return paths

def extract(path):
    p=subprocess.run([str(INTERFACE),str(path)],capture_output=True,text=True,timeout=10);p.check_returncode();api=json.loads(p.stdout)
    if api['status']!='inspected':raise RuntimeError(api)
    dump(path.with_suffix(path.suffix+'.api.json'),api);return api

def summarize(rows):
    summary={}
    for caller in ['null','typed']:
      for observer in ['flat','multi']:
        for en in ['node','spidermonkey']:
          rs=[r for r in rows if (r['caller'],r['observer'],r['engine'],r['level'])==(caller,observer,en,'O0')];cs=collections.Counter();known=collections.Counter();unsupported=collections.Counter()
          for r in rs:
            if r.get('study'):
              for call in r['study']['calls']:
                cs[call['status']]+=1
                if call['known']:known[call['status']]+=1
                if call['unsupported']:unsupported[call['status']]+=1
          ds=[r['study'] for r in rs if r.get('study')]
          summary['%s-%s-%s'%(caller,observer,en)]=dict(processes=len(rs),process_status=dict(collections.Counter(r['status'] for r in rs)),instantiation_failed=sum(r['instantiation_failed'] for r in rs),call_status=dict(cs),known_call_status=dict(known),unsupported_parameter_calls=dict(unsupported),modules_with_gc_events=sum(s['events']>0 for s in ds),modules_with_repeated_identity=sum(s['events']>s['distinct'] for s in ds),gc_events=sum(s['events'] for s in ds),multi_slots=sum(s['multi_slots'] for s in ds),median_process_ms=statistics.median(r['wall_ms'] for r in rs))
    return summary

def semantic_trace(study):
    # A function can acquire a different first export alias after merging.
    # Keep that diagnostic label in raw data, but do not treat it as semantics.
    return [(e['id'],e['channel'],e['slot']) for e in study['trace']]

def main(out,seeds):
    out.mkdir(parents=True,exist_ok=False);shells=make_shells(out);rows=[];metadata=[]
    for seed in range(seeds):
      for level in ['O0','O3']:
        path=out/('%d-%s.wasm'%(seed,level));shutil.copy2(SOURCE/path.name,path);api=extract(path)
        metadata.append(dict(seed=seed,level=level,file=path.name,sha256=sha(path),api_sha256=sha(path.with_suffix('.wasm.api.json'))))
        for (caller,observer),shell in shells.items():
          for en,exe in [('node','node'),('spidermonkey',str(SM))]:
            r=run([exe,shell,path],3);name='%d-%s-%s-%s-%s'%(seed,level,caller,observer,en);stdout=r.pop('stdout');stderr=r.pop('stderr')
            (out/(name+'.stdout')).write_text(stdout,encoding='utf8');(out/(name+'.stderr')).write_text(stderr,encoding='utf8')
            line=next((s for s in stdout.splitlines() if s.startswith('[caller-study] ')),None)
            rows.append(dict(seed=seed,level=level,caller=caller,observer=observer,engine=en,stdout_file=name+'.stdout',stderr_file=name+'.stderr',study=json.loads(line[len('[caller-study] '):]) if line else None,instantiation_failed='failed to instantiate module' in stdout,**r))
      if seed%16==0:print(json.dumps(dict(seed=seed,processes=len(rows))),flush=True)
    comparisons=[];cross=[];baseline=[]
    for seed in range(seeds):
      for caller,observer in shells:
        for en in ['node','spidermonkey']:
          pair=[r for r in rows if (r['seed'],r['caller'],r['observer'],r['engine'])==(seed,caller,observer,en)]
          if len(pair)==2 and all(r['study'] is not None for r in pair):
            comparisons.append(dict(seed=seed,caller=caller,observer=observer,engine=en,trace_equal=semantic_trace(pair[0]['study'])==semantic_trace(pair[1]['study']),calls_equal=[c['status'] for c in pair[0]['study']['calls']]==[c['status'] for c in pair[1]['study']['calls']],metadata_call_labels_equal=[c['name'] for c in pair[0]['study']['calls']]==[c['name'] for c in pair[1]['study']['calls']]))
        for level in ['O0','O3']:
          pair=[r for r in rows if (r['seed'],r['caller'],r['observer'],r['level'])==(seed,caller,observer,level)]
          if len(pair)==2 and all(r['study'] is not None for r in pair):cross.append(dict(seed=seed,caller=caller,observer=observer,level=level,trace_equal=semantic_trace(pair[0]['study'])==semantic_trace(pair[1]['study'])))
    old={(r['seed'],r['level'],r['engine']):r for r in json.loads((SOURCE/'rows.json').read_text())}
    for r in rows:
      if r['caller']=='null' and r['observer']=='flat' and r['study']:
        baseline.append(dict(seed=r['seed'],level=r['level'],engine=r['engine'],equal=[e['id'] for e in r['study']['trace']]==old[r['seed'],r['level'],r['engine']]['alias']['trace']))
    report=dict(comparison_version=2,seeds=seeds,processes=len(rows),interface_tool_sha256=sha(INTERFACE),printer_sha256=sha(PRINTER),summary=summarize(rows),optimization_comparisons=comparisons,cross_engine_comparisons=cross,old_baseline_replay=baseline)
    dump(out/'rows.json',rows);dump(out/'metadata.json',metadata);dump(out/'report.json',report)
    dump(out/'manifest.json',[dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()]);print(json.dumps(dict(seeds=seeds,processes=len(rows),summary=report['summary'],optimization_trace_differences=sum(not x['trace_equal'] for x in comparisons),optimization_call_differences=sum(not x['calls_equal'] for x in comparisons),cross_differences=sum(not x['trace_equal'] for x in cross),baseline_differences=sum(not x['equal'] for x in baseline)),indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--seeds',type=int,default=64);a=ap.parse_args();main(a.out.resolve(),a.seeds)
