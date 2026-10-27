"""Use the same O0 observer on real Binaryen outputs and their O3 versions."""
import argparse,collections,importlib.util,json,shutil,subprocess,time
from pathlib import Path
from experiment import ROOT,HERE,TOOL,SM,dump,sha
import sys
sys.path.insert(0,str(ROOT/'research/boundary-alias'))
saved_experiment=sys.modules.pop('experiment')
try:
 spec=importlib.util.spec_from_file_location('ce',ROOT/'research/boundary-alias/caller-experiment.py');ce=importlib.util.module_from_spec(spec);spec.loader.exec_module(ce)
finally:
 sys.modules['experiment']=saved_experiment
SOURCE=ROOT/'results/boundary-alias/caller-v1'

def shell(out):
 source=ce.PRINTER.read_text();hook=(ROOT/'research/boundary-alias/caller-hook.js').read_text().replace('__CALLER__','typed').replace('__OBSERVER__','multi')
 observer=(HERE/'observe.js').read_text().replace("if(typeof module!=='undefined')module.exports={heapSnapshot};",'')
 extra='''
var __observerPrefix=argv[0].replace(/-[A-Z][0-9]+\\.wasm$/,'.observer');
var __observerMeta=JSON.parse(__readText(__observerPrefix+'.json'));
var __observerExports=new WebAssembly.Instance(new WebAssembly.Module(readBinary(__observerPrefix+'.wasm'))).exports;
var __snapshots=[],__snapshotLimit=128,__observationErrors=[];
var __previousObserve=__observe;
__observe=function(x,channel,name,slot){
  var before=__trace.length;__previousObserve(x,channel,name,slot);
  if(__trace.length!==before&&__snapshots.length<__snapshotLimit){
    try{__snapshots.push({channel:channel,slot:slot,snapshot:heapSnapshot([x],__observerExports,__observerMeta,{nodes:32,elements:8})});}
    catch(e){__observationErrors.push({channel:channel,slot:slot,error:String(e)});}
  }
};
'''
 tail="\nconsole.log('[heap-study] '+JSON.stringify({calls:__calls,trace:__trace,snapshots:__snapshots,observation_errors:__observationErrors,events:__trace.length,limit:__snapshotLimit}));\n"
 text=source.replace('rawExports[key] = value;','rawExports[key] = value; __registerExport(key, value);').replace('// Build the main wasm.',hook+'\n'+observer+'\n'+extra+'\n// Build the main wasm.')+tail
 p=out/'shell.js';p.write_text(text);shutil.copy2(SOURCE/'classifier.wasm',out/'classifier.wasm');return p

def main(out):
 out.mkdir(parents=True,exist_ok=False);sh=shell(out);rows=[];generation=[];baseline=[]
 old={(r['seed'],r['level'],r['engine']):r for r in json.loads((SOURCE/'rows.json').read_text()) if r['caller']=='typed' and r['observer']=='multi'}
 for seed in range(64):
  raw=SOURCE/('%d-O0.wasm'%seed);helper=out/('%d.observer.wasm'%seed)
  t=time.perf_counter_ns();p=subprocess.run([str(TOOL),str(raw),str(helper)],capture_output=True,text=True,timeout=10);meta=json.loads(p.stdout);ms=(time.perf_counter_ns()-t)/1e6
  dump(out/('%d.observer.json'%seed),meta);generation.append(dict(seed=seed,generation_ms=ms,**meta))
  if meta['status']!='generated':continue
  for level in ['O0','O3']:
   path=out/('%d-%s.wasm'%(seed,level));shutil.copy2(SOURCE/path.name,path);shutil.copy2(SOURCE/(path.name+'.api.json'),out/(path.name+'.api.json'))
   for en,exe in [('node','node'),('spidermonkey',str(SM))]:
    rr=ce.run([exe,sh,path],5);stdout=rr.pop('stdout');stderr=rr.pop('stderr');stem=path.stem+'-'+en;(out/(stem+'.stdout')).write_text(stdout);(out/(stem+'.stderr')).write_text(stderr)
    line=next((x[len('[heap-study] '):] for x in stdout.splitlines() if x.startswith('[heap-study] ')),None);study=json.loads(line) if line else None
    rows.append(dict(seed=seed,level=level,engine=en,study=study,instantiation_failed='failed to instantiate module' in stdout,**rr))
    if study:
     o=old[seed,level,en]['study'];baseline.append(dict(seed=seed,level=level,engine=en,calls_equal=[c['status'] for c in study['calls']]==[c['status'] for c in o['calls']],trace_equal=ce.semantic_trace(study)==ce.semantic_trace(o)))
  if seed%16==0:print(json.dumps(dict(seed=seed,runs=len(rows))),flush=True)
 comparisons=[];cross=[]
 for r in rows:
  if r['study'] is None:continue
  if r['level']=='O0':
   pair=next(s for s in rows if (s['seed'],s['level'],s['engine'])==(r['seed'],'O3',r['engine']))
   comparisons.append(dict(seed=r['seed'],engine=r['engine'],compared=pair['study'] is not None,equal=pair['study'] is not None and r['study']['snapshots']==pair['study']['snapshots']))
  if r['engine']=='node':
   pair=next(s for s in rows if (s['seed'],s['level'],s['engine'])==(r['seed'],r['level'],'spidermonkey'))
   cross.append(dict(seed=r['seed'],level=r['level'],compared=pair['study'] is not None,equal=pair['study'] is not None and r['study']['snapshots']==pair['study']['snapshots']))
 sample=[r for r in rows if r['level']=='O0' and r['engine']=='node' and r['study']]
 report=dict(seeds=64,generation_status=dict(collections.Counter(g['status'] for g in generation)),rejection_reasons=dict(collections.Counter(g.get('reason') for g in generation if g['status']!='generated')),processes=len(rows),process_status=dict(collections.Counter(r['status'] for r in rows)),instantiation_failed=sum(r['instantiation_failed'] for r in rows),observation_errors=sum(len(r['study']['observation_errors']) for r in rows if r['study']),modules_with_snapshots=sum(bool(r['study']['snapshots']) for r in sample),snapshots_O0_node=sum(len(r['study']['snapshots']) for r in sample),objects_O0_node=sum(len(s['snapshot']['objects']) for r in sample for s in r['study']['snapshots']),truncations_O0_node=sum(s['snapshot']['truncations'] for r in sample for s in r['study']['snapshots']),unknown_objects_O0_node=sum('opaque' in o for r in sample for s in r['study']['snapshots'] for o in s['snapshot']['objects']),optimization_comparisons=comparisons,cross_engine_comparisons=cross,baseline=baseline)
 dump(out/'rows.json',rows);dump(out/'generation.json',generation);dump(out/'report.json',report);dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()])
 print(json.dumps({k:v for k,v in report.items() if k not in ['optimization_comparisons','cross_engine_comparisons','baseline']},indent=2));print(json.dumps(dict(optimization_differences=sum(not p['equal'] for p in comparisons),cross_differences=sum(not p['equal'] for p in cross),baseline_differences=sum(not p['calls_equal'] or not p['trace_equal'] for p in baseline))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out.resolve())
