"""Predicted misses from finite observation limits; these are not engine bugs."""
import argparse,json,subprocess
from pathlib import Path
from experiment import HERE,TOOL,SM,OPT,FEATURES,wt,dump,sha
def main(out):
 out.mkdir(parents=True,exist_ok=False);rows=[];errors=[]
 for family in ['null','empty','late-array','deep-node']:
  helper=out/(family+'.observer.wasm');mp=out/(family+'.observer.json')
  for variant in ['base','changed']:
   n=43 if variant=='changed' else 42
   if family=='null':wat='(module (func (export "get") (result anyref) ref.null any))'
   elif family=='empty':wat='(module (type $s (array i32)) (global $g (ref $s) (array.new $s (i32.const 0) (i32.const 0))) (func (export "get") (result anyref) global.get $g))'
   elif family=='late-array':wat=f'(module (type $s (array (mut i32))) (global $g (ref $s) (array.new $s (i32.const 42) (i32.const 64))) (func $init (array.set $s (global.get $g) (i32.const 63) (i32.const {n}))) (start $init) (func (export "get") (result anyref) global.get $g))'
   else:wat=f'(module (type $s (struct (field (ref null $s)) (field i32))) (global $g (ref $s) (struct.new $s (struct.new $s (ref.null $s) (i32.const {n})) (i32.const 7))) (func (export "get") (result anyref) global.get $g))'
   raw=out/(family+'-'+variant+'-O0.wasm');raw.with_suffix('.wat').write_text(wat);raw.write_bytes(wt.wat2wasm(wat))
   if variant=='base':
    p=subprocess.run([str(TOOL),str(raw),str(helper)],capture_output=True,text=True,timeout=10);meta=json.loads(p.stdout);assert meta['status']=='generated';dump(mp,meta)
   for level in ['O0','O3']:
    path=raw if level=='O0' else out/(family+'-'+variant+'-O3.wasm')
    if level=='O3':subprocess.run([str(OPT),str(raw),*FEATURES,'-O3','-o',str(path)],capture_output=True,timeout=10,check=True)
    for cap in ['limited','full']:
     limits={'nodes':1 if cap=='limited' else 32,'elements':8 if cap=='limited' else 64}
     for en,exe in [('node','node'),('spidermonkey',str(SM))]:
      p=subprocess.run([exe,str(HERE/'runner.js'),str(path),str(helper),str(mp),str(HERE/'observe.js'),json.dumps(limits)],capture_output=True,text=True,timeout=5);r=json.loads(p.stdout);rows.append(dict(family=family,variant=variant,level=level,cap=cap,engine=en,result=r));assert r['status']=='observed'
 comparisons=[]
 for family in ['null','empty','late-array','deep-node']:
  for level in ['O0','O3']:
   for cap in ['limited','full']:
    for en in ['node','spidermonkey']:
     pair=[r for r in rows if (r['family'],r['level'],r['cap'],r['engine'])==(family,level,cap,en)];equal=pair[0]['result']['snapshot']==pair[1]['result']['snapshot'];expected=family in ['null','empty'] or cap=='limited';passed=equal==expected;comparisons.append(dict(family=family,level=level,cap=cap,engine=en,equal=equal,expected_equal=expected,passed=passed))
     if not passed:errors.append(comparisons[-1])
 dump(out/'rows.json',rows);dump(out/'report.json',dict(binaries=16,processes=len(rows),comparisons=comparisons,errors=errors));dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()]);print(json.dumps(dict(processes=len(rows),comparisons=len(comparisons),errors=errors)));assert not errors
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out.resolve())
