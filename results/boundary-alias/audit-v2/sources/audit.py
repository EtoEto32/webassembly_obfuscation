"""Rebuild, reclassify and recompute the bounded study without editing raw results."""
import argparse,collections,json,statistics,subprocess,sys
from pathlib import Path
from experiment import ROOT,HERE,OPT,SM,FEATURES,wt,dump,sha,module

def main(out):
 out.mkdir(parents=True,exist_ok=False);errors=[];checked=0;rebuilt=0
 dirs=[ROOT/'results/type-context/priors-v2',ROOT/'results/type-context/more-priors-v2',ROOT/'results/type-context/v8-prior-v1',ROOT/'results/type-context/binaryen-baseline-v1']+[ROOT/'results/boundary-alias'/d for d in ['probe-v2','binaryen-v1','binaryen-v2','performance-v1','priors-v1']]
 for directory in dirs:
  for row in json.loads((directory/'manifest.json').read_text()):
   if row.get('status')=='unavailable':continue
   p=directory/row['file'];checked+=1
   if sha(p)!=row['sha256']:errors.append(dict(kind='hash',file=str(p)))
 source=ROOT/'results/boundary-alias/probe-v2';cases=json.loads((source/'cases.json').read_text())
 for row in cases:
  if row['level']=='O0':data=wt.wat2wasm(module(row['kind'],row['family'],row['variant']))
  else:
   target=out/row['file'];p=subprocess.run([str(OPT),str(source/(row['name']+'-O0.wasm')),*FEATURES,'-'+row['level'],'-o',str(target)],capture_output=True,text=True,timeout=20);p.check_returncode();data=target.read_bytes()
  rebuilt+=1
  if data!=(source/row['file']).read_bytes():errors.append(dict(kind='rebuild',file=row['file']))
 cal=[]
 for en,exe in [('node','node'),('spidermonkey',str(SM))]:
  p=subprocess.run([exe,str(HERE/'check-classifier.js'),str(ROOT/'results/boundary-alias/binaryen-v2'),str(source)],capture_output=True,text=True,timeout=10);p.check_returncode();r=json.loads(p.stdout);dump(out/(en+'-classifier.json'),r);cal.append(dict(engine=en,cases=len(r['rows']),errors=r['errors']));errors.extend(r['errors'])
 real=ROOT/'results/boundary-alias/binaryen-v2';rs=json.loads((real/'rows.json').read_text());pr=json.loads((real/'report.json').read_text());classification=[];cross=[];text_differences=[];same_guests=0
 for r in rs:
  log=(real/r['stdout_file']).read_text();line=next(x for x in log.splitlines() if x.startswith('[boundary-alias] '));alias=json.loads(line[17:])
  if alias!=r['alias']:errors.append(dict(kind='alias-reparse',file=r['file']))
  exceptions=collections.Counter()
  for s in log.splitlines():
   if s.startswith('exception thrown: '):
    kind=s[len('exception thrown: '):].split(':')[0];exceptions[kind]+=1
  classification.append(dict(seed=r['seed'],level=r['level'],engine=r['engine'],caught_exceptions=dict(exceptions),events=alias['events'],distinct=alias['distinct']))
 for seed in range(64):
  for level in ['O0','O3']:
   pair=[r for r in rs if r['seed']==seed and r['level']==level]
   if len(pair)!=2 or pair[0]['alias']!=pair[1]['alias']:cross.append(dict(seed=seed,level=level))
   a=real/('%d-%s.wasm'%(seed,level));b=ROOT/'results/boundary-alias/binaryen-v1'/a.name
   if a.read_bytes()==b.read_bytes():same_guests+=1
   else:errors.append(dict(kind='v1-v2-guest',file=a.name))
  for en in ['node','spidermonkey']:
   def original(level):return [s for s in (real/('%d-%s-%s.stdout'%(seed,level,en))).read_text().splitlines() if not s.startswith('[boundary-alias] ')]
   if original('O0')!=original('O3'):text_differences.append(dict(seed=seed,engine=en))
 exceptions=collections.Counter()
 for r in classification:exceptions.update(r['caught_exceptions'])
 unique=[r for r in classification if r['engine']=='node' and r['level']=='O0']
 # Independently rederive timing summaries from each fresh process result.
 performance=ROOT/'results/boundary-alias/performance-v1';summaries=json.loads((performance/'summary.json').read_text());timings=0
 for r in summaries:
  vals=[json.loads((performance/('%d-%s-%s-%d.json'%(r['n'],r['pattern'],r['mode'],i))).read_text()) for i in range(3)]
  med=statistics.median(statistics.median(s['ns_per_event'] for s in v['samples']) for v in vals);timings+=1
  if med!=r['median_ns_per_event']:errors.append(dict(kind='timing',condition=r))
 report=dict(manifests=len(dirs),files_checked=checked,binaries_rebuilt=rebuilt,timing_conditions=timings,classifier_calibration=cal,real_generator=dict(modules=64,all_validated=all(r['validation']=='passed' for r in rs),binary_pairs_equal=all(c['equal'] for c in pr['comparisons']),cross_engine_differences=cross,original_stdout_differences=text_differences,v1_v2_same_binaries=same_guests,modules_with_gc_events=sum(r['events']>0 for r in unique),modules_with_repeated_identity=sum(r['events']>r['distinct'] for r in unique),repeated_seeds=[r['seed'] for r in unique if r['events']>r['distinct']],instantiation_failure_seeds=[r['seed'] for r in unique if r['caught_exceptions'].get('failed to instantiate module')],event_total=sum(r['events'] for r in unique),caught_guest_exceptions=dict(exceptions)),errors=errors)
 dump(out/'guest-outcomes.json',classification);dump(out/'report.json',report)
 sources=out/'sources';sources.mkdir()
 for p in sorted(HERE.iterdir()):
  if p.suffix in ['.py','.js','.md']:(sources/p.name).write_bytes(p.read_bytes())
 dump(out/'manifest.json',[dict(file=str(p.relative_to(out)),sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()]);print(json.dumps(report,indent=2));assert not errors and not cross
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out.resolve())
