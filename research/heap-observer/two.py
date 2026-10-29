"""The existing Two handler's generator and linked execution, with bounded budgets."""
import argparse,ast,collections,json,random,re,shutil,subprocess,time,os
from pathlib import Path
from experiment import ROOT,HERE,OPT,SM,FEATURES,wt,dump,sha,fixture
from generated import ce
FUZZ=ROOT/'results/heap-observer/priors-v1/binaryen-fuzz_opt.py'
PRINTER=ce.PRINTER

def upstream_normalizer():
 tree=ast.parse(FUZZ.read_text(encoding='utf8'));fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fix_output')
 env=dict(re=re,TRAP_PREFIX='[trap ',EXCEPTION_PREFIX='exception thrown: ',INSTANTIATE_ERROR='exception thrown: failed to instantiate module')
 exec(compile(ast.Module(body=[fun],type_ignores=[]),str(FUZZ),'exec'),env)
 return env['fix_output']

def make_shell(out):
 source=PRINTER.read_text(encoding='utf8');hook=(ROOT/'research/boundary-alias/caller-hook.js').read_text().replace('__CALLER__','typed').replace('__OBSERVER__','multi')
 line="var __api = JSON.parse(__readText(argv[0] + '.api.json'));";assert hook.count(line)==1
 hook=hook.replace(line,line+"\nvar __firstApi=__api,__secondApi=JSON.parse(__readText(argv[1]+'.api.json'));")
 hook=hook.replace('function __registerExport(key, value) {','function __registerExport(key, value, isSecond) {\n  var __api=isSecond?__secondApi:__firstApi;')
 tail="\nconsole.log('[caller-study] '+JSON.stringify({calls:__calls,trace:__trace}));\n"
 text=source.replace('rawExports[key] = value;','rawExports[key] = value; __registerExport(key, value, isSecond);').replace('// Build the main wasm.',hook+'\n// Build the main wasm.')+tail
 shell=out/'typed-two-shell.js';shell.write_text(text,encoding='utf8');shutil.copy2(ROOT/'results/boundary-alias/caller-v1/classifier.wasm',out/'classifier.wasm');return shell

def main(out,count,interface):
 os.environ['BINARYEN_MAX_INTERPRETER_DEPTH']='1000'
 out.mkdir(parents=True,exist_ok=False);typed_shell=make_shell(out);normalize=upstream_normalizer();rows=[];generation=[];comparisons=[]
 families=['scalar','packed','array','deep','alias','cycle','recgroup','subtype','nan-positive','scalar-visible']
 for family in families:
  for variant in ['base','changed']:
   raw=out/(family+'-'+variant+'.wasm')
   wat=fixture(family,variant) if family!='scalar-visible' else '(module (func (export "get") (result i32) i32.const %d))'%(42 if variant=='changed' else 41)
   if interface=='concrete' and family!='scalar-visible':wat=wat.replace('(result anyref)','(result (ref $s))')
   raw.with_suffix('.wat').write_text(wat);raw.write_bytes(wt.wat2wasm(wat));ce.extract(raw)
  base=out/(family+'-base.wasm')
  for seed in range(count):
   rng=random.Random(202610270300+seed);inp=out/('%s-%d.seed'%(family,seed));inp.write_bytes(bytes(rng.getrandbits(8) for _ in range(1024)));second=out/('%s-%d.second.wasm'%(family,seed))
   cmd=[OPT,inp,'-ttf','--fuzz-import='+str(base),'--remove-start','--no-fuzz-memory','--no-fuzz-oob',*FEATURES,'-o',second];g=ce.run(cmd,10);generation.append(dict(family=family,seed=seed,command=list(map(str,cmd)),**g))
   if g['status']!='completed':continue
   ce.extract(second)
   for method in ['bynterp','upstream-node','typed-node']:
    pair=[]
    for variant in ['base','changed']:
     raw=out/(family+'-'+variant+'.wasm')
     if method=='bynterp':cmd=[OPT,raw,*FEATURES,'--fuzz-exec-before','--fuzz-exec-second='+str(second)]
     else:cmd=['node',PRINTER if method=='upstream-node' else typed_shell,raw,second]
     r=ce.run(cmd,3);stdout=r.pop('stdout');stderr=r.pop('stderr');stem='%s-%d-%s-%s'%(family,seed,method,variant);(out/(stem+'.stdout')).write_text(stdout,encoding='utf8');(out/(stem+'.stderr')).write_text(stderr,encoding='utf8')
     line=next((x[15:] for x in stdout.splitlines() if x.startswith('[caller-study] ')),None);study=json.loads(line) if line else None;plain='\n'.join(x for x in stdout.splitlines() if not x.startswith('[caller-study] '))
     norm=normalize(plain);(out/(stem+'.normalized')).write_text(norm,encoding='utf8')
     row=dict(family=family,seed=seed,method=method,variant=variant,stdout_file=stem+'.stdout',stderr_file=stem+'.stderr',normalized_file=stem+'.normalized',study=study,instantiation_failed='failed to instantiate module' in stdout,**r);rows.append(row);pair.append((row,norm))
    eligible=all(r['status']=='completed' and not r['instantiation_failed'] for r,n in pair)
    comparisons.append(dict(family=family,seed=seed,method=method,eligible=eligible,output_difference=eligible and pair[0][1]!=pair[1][1],semantic_trace_difference=eligible and method=='typed-node' and ce.semantic_trace(pair[0][0]['study'])!=ce.semantic_trace(pair[1][0]['study']),call_status_difference=eligible and method=='typed-node' and [c['status'] for c in pair[0][0]['study']['calls']]!=[c['status'] for c in pair[1][0]['study']['calls']],generation_ms=g['wall_ms'],execution_pair_ms=sum(r['wall_ms'] for r,n in pair)))
  print(json.dumps(dict(family=family,contexts=count,runs=len(rows))),flush=True)
  dump(out/'progress.json',dict(last_family=family,contexts=count,runs=len(rows),interface=interface))
 summary={}
 for method in ['bynterp','upstream-node','typed-node']:
  summary[method]={family:dict(contexts=sum(c['family']==family and c['method']==method for c in comparisons),eligible=sum(c['family']==family and c['method']==method and c['eligible'] for c in comparisons),detected=sum(c['family']==family and c['method']==method and (c['output_difference'] or c['semantic_trace_difference'] or c['call_status_difference']) for c in comparisons)) for family in families}
 report=dict(interface=interface,max_interpreter_depth=1000,contexts_per_family=count,families=len(families),processes=len(rows),generation_status=dict(collections.Counter(g['status'] for g in generation)),process_status=dict(collections.Counter(r['status'] for r in rows)),summary=summary,comparisons=comparisons,upstream_normalization_sha256=sha(FUZZ),upstream_shell_sha256=sha(PRINTER),limitations=['selected Two generator/linking paths only; no merge campaign','fixed small synthetic families','three second per-execution limit','same seed sequence across families'])
 dump(out/'rows.json',rows);dump(out/'generation.json',generation);dump(out/'report.json',report);dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()]);print(json.dumps({k:v for k,v in report.items() if k not in ['comparisons','limitations']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('--contexts',type=int,default=4);p.add_argument('--interface',choices=['abstract','concrete'],default='abstract');a=p.parse_args();main(a.out.resolve(),a.contexts,a.interface)
