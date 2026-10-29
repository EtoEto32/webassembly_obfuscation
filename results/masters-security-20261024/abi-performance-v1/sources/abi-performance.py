"""Bounded performance comparison including a correct non-memo preflight."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(source,out):
 hashes=json.loads((source/'sha256.json').read_text())
 for relative,digest in hashes.items():assert sha(source/relative)==digest
 out.mkdir(parents=True,exist_ok=False);(out/'sources').mkdir()
 for name in ('abi-performance.py','abi-performance.cjs','abi-performance-plan.md'):shutil.copy2(HERE/name,out/'sources'/name)
 jobs=[(r,m) for r in range(5) for m in ('late','tree','memo')];random.Random(2026102404).shuffle(jobs)
 (out/'jobs.json').write_text(json.dumps(jobs));results=[]
 for rep,mode in jobs:
  target=out/(str(rep)+'-'+mode+'.json');r=subprocess.run(['node','--expose-gc',str(HERE/'abi-performance.cjs'),str(source),mode,str(target)],capture_output=True,text=True,timeout=60)
  (out/(target.stem+'.log')).write_text(r.stdout+r.stderr,encoding='utf8');assert r.returncode==0,r.stderr
  results.append({'rep':rep,**json.loads(target.read_text())})
 rows=[]
 for name in [r['name'] for r in results[0]['rows']]:
  def median(x):return statistics.median(next(r['samples_us'] for r in x['rows'] if r['name']==name))
  tree={x['rep']:median(x) for x in results if x['mode']=='tree'}
  for mode in ('late','tree','memo'):
   selected=[x for x in results if x['mode']==mode];samples=[median(x) for x in selected];q=statistics.quantiles(samples,n=4,method='inclusive')
   rows.append({'case':name,'mode':mode,'median_us':statistics.median(samples),'iqr_us':q[2]-q[0],
     'processMedians':samples,'ratioToTree':statistics.median([median(x)/tree[x['rep']] for x in selected])})
 summary={'processes':15,'rows':rows,'input':{'path':str(source),'hashes':hashes},
  'scope':'fixed one-page Component, logical units budget, full guest setup included; not Wasmtime fuel comparison'}
 (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
 lines=['# 展開前検査の補助実験','','5 process中央値。µs。treeは同じ予算を守る正しい非memo方式。','','|case|mode|median|IQR|ratio/tree|','|---|---|---:|---:|---:|']
 lines+=['|{case}|{mode}|{median_us:.3f}|{iqr_us:.3f}|{ratioToTree:.3f}|'.format(**x) for x in rows]
 (out/'report.md').write_text('\n'.join(lines),encoding='utf8')
 (out/'sha256.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},indent=2))
 print(json.dumps({'processes':15,'memoToTree':[x['ratioToTree'] for x in rows if x['mode']=='memo']}))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
