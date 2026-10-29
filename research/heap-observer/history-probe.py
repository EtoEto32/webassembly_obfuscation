"""A source-identified regression adapted to expose its result, not a new bug claim."""
import argparse,json,subprocess
from pathlib import Path
from experiment import ROOT,HERE,OPT,TOOL,SM,wt,FEATURES,dump,sha
from generated import ce
OLD=ROOT/'.tools/heap-observer-binaryen-123/wasm-opt.exe'
def module(form):
 prefix='''(module
 (type $empty (struct))
 (type $referrer (struct (field (mut (ref null $empty)))))
 (type $box (struct (field i32)))
 (func (export "get") (result %s)
 (local $A (ref $referrer)) (local $B (ref $empty)) (local $A2 (ref $referrer))
 (local.set $A2 (local.tee $A (struct.new $referrer (local.tee $B (struct.new_default $empty)))))
 %s))'''
 test='(ref.eq (local.get $A) (local.get $A2))'
 if form=='scalar':return prefix%('i32',test)
 return prefix%('anyref' if form=='boxed-abstract' else '(ref $box)','(struct.new $box '+test+')')

def main(out):
 out.mkdir(parents=True,exist_ok=False);rows=[]
 for form in ['scalar','boxed-abstract','boxed-concrete']:
  raw=out/(form+'-O0.wasm');wat=module(form);raw.with_suffix('.wat').write_text(wat);raw.write_bytes(wt.wat2wasm(wat));helper=out/(form+'.observer.wasm');mp=out/(form+'.observer.json')
  p=subprocess.run([str(TOOL),str(raw),str(helper)],capture_output=True,text=True,timeout=10);meta=json.loads(p.stdout);assert meta['status']=='generated';dump(mp,meta)
  for compiler,tool in [('none',None),('binaryen123',OLD),('binaryen133',OPT)]:
   path=raw if tool is None else out/(form+'-'+compiler+'.wasm')
   if tool:
    r=ce.run([tool,raw,*FEATURES,'--precompute-propagate','-o',path],10);dump(out/(path.stem+'.opt.json'),r)
    if r['status']!='completed':rows.append(dict(form=form,compiler=compiler,kind='optimizer',**r));continue
   for en,exe in [('node','node'),('spidermonkey',str(SM))]:
    normal=ce.run([exe,ce.PRINTER,path],5);obs=ce.run([exe,HERE/'runner.js',path,helper,mp,HERE/'observe.js'],5)
    prefix=form+'-'+compiler+'-'+en;dump(out/(prefix+'.plain.json'),normal);dump(out/(prefix+'.observed.json'),obs)
    rows.append(dict(form=form,compiler=compiler,engine=en,plain=normal['stdout'],observed=json.loads(obs['stdout']),normal_status=normal['status'],observation_status=obs['status']))
 report=dict(source_pr='https://github.com/WebAssembly/binaryen/pull/7857',adaptation='Extract nested struct creation and first ref.eq; add export and return, optionally box result in a new i32 field. Not the exact upstream test.',old_tool_sha256=sha(OLD),current_tool_sha256=sha(OPT),rows=rows)
 dump(out/'report.json',report);dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()]);print(json.dumps([dict(form=r['form'],compiler=r['compiler'],engine=r.get('engine'),plain=r.get('plain'),observed=r.get('observed')) for r in rows],indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out.resolve())
