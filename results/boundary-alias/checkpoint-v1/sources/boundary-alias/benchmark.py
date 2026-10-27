import argparse,json,statistics,subprocess
from pathlib import Path
from experiment import HERE,dump,sha
def main(source,out):
 out.mkdir(parents=True,exist_ok=False);rows=[]
 for n in [64,256,1024,4096]:
  for pattern in ['shared','eight','unique']:
   for repeat in range(3):
    for mode in ['printed','weak','linear']:
     p=subprocess.run(['node','--expose-gc',str(HERE/'benchmark.js'),str(source),str(n),pattern,mode],capture_output=True,text=True,timeout=20);p.check_returncode();r=json.loads(p.stdout);r['process_repeat']=repeat
     name='%d-%s-%s-%d.json'%(n,pattern,mode,repeat);dump(out/name,r);rows.append(r)
 summary=[]
 for n in [64,256,1024,4096]:
  for pattern in ['shared','eight','unique']:
   for mode in ['printed','weak','linear']:
    rs=[r for r in rows if (r['n'],r['pattern'],r['mode'])==(n,pattern,mode)];process_medians=[statistics.median(s['ns_per_event'] for s in r['samples']) for r in rs]
    summary.append(dict(n=n,pattern=pattern,mode=mode,processes=len(rs),median_ns_per_event=statistics.median(process_medians),min_process_median=min(process_medians),max_process_median=max(process_medians),median_heap_delta_bytes=statistics.median(s['heap_delta_bytes'] for r in rs for s in r['samples']),max_rss_kib=max(r['process_max_rss_kib'] for r in rs)))
 dump(out/'summary.json',summary);dump(out/'manifest.json',[dict(file=p.name,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()]);print(json.dumps(dict(processes=len(rows),conditions=len(summary),n4096=[x for x in summary if x['n']==4096]),indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('out',type=Path);a=ap.parse_args();main(a.source.resolve(),a.out.resolve())
