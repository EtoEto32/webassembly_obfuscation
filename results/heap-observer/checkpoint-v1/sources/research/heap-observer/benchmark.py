import argparse,json,statistics,subprocess
from pathlib import Path
from experiment import HERE,TOOL,wt,dump,sha
def main(out):
 out.mkdir(parents=True,exist_ok=False);rows=[]
 for n in [0,8,64,1024]:
  wat=f'(module (type $s (array i32)) (global $g (ref $s) (array.new $s (i32.const 42) (i32.const {n}))) (func (export "get") (result anyref) global.get $g))';raw=out/('%d.wasm'%n);raw.write_bytes(wt.wat2wasm(wat));raw.with_suffix('.wat').write_text(wat);helper=out/('%d.observer.wasm'%n);mp=out/('%d.observer.json'%n)
  p=subprocess.run([str(TOOL),str(raw),str(helper)],capture_output=True,text=True,timeout=10);meta=json.loads(p.stdout);assert meta['status']=='generated';dump(mp,meta)
  for mode in ['boundary','cap8','full','manualcap8','manualfull']:
   for rep in range(3):
    p=subprocess.run(['node','--expose-gc',str(HERE/'bench.js'),str(raw),str(helper),str(mp),mode,str(n)],capture_output=True,text=True,timeout=20);p.check_returncode();row=json.loads(p.stdout);row['rep']=rep;rows.append(row)
 summaries=[]
 for n in [0,8,64,1024]:
  for mode in ['boundary','cap8','full','manualcap8','manualfull']:
   group=[r for r in rows if r['n']==n and r['mode']==mode];medians=[statistics.median(r['samples']) for r in group];summaries.append(dict(n=n,mode=mode,processes=len(group),median_ns=statistics.median(medians),min_process_median_ns=min(medians),max_process_median_ns=max(medians),median_heap_delta=statistics.median(r['heap_delta'] for r in group),median_rss=statistics.median(r['rss'] for r in group),output_bytes=group[0]['output_bytes']))
 dump(out/'rows.json',rows);dump(out/'report.json',dict(processes=len(rows),summary=summaries));dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()]);print(json.dumps(summaries,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out.resolve())
