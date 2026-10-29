"""Bounded copies of the two primary papers used to reject a generic call-pool novelty claim."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
URLS={'randoop.pdf':'https://homes.cs.washington.edu/~mernst/pubs/feedback-testgen-icse2007.pdf','weaver.html':'https://arxiv.org/html/2603.18789v1'}
def main(out):
 out.mkdir(parents=True,exist_ok=False);rows=[]
 for name,url in URLS.items():
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research/1.0'}),timeout=25) as r:data=r.read(10000001)
   if len(data)>10000000:raise ValueError('size cap')
   (out/name).write_bytes(data);rows.append(dict(file=name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),status='downloaded'))
  except Exception as e:rows.append(dict(file=name,url=url,status='unavailable',error=str(e)))
 (out/'manifest.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
