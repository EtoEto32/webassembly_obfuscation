import argparse,hashlib,json,urllib.request
from pathlib import Path
NUMBERS=[9254,9242,9209,9108,9043,7857,7863,6834]
def main(out):
 out.mkdir(parents=True,exist_ok=False);manifest=[]
 for number in NUMBERS:
  url='https://api.github.com/repos/WebAssembly/binaryen/pulls/%d/files?per_page=100'%number
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research/1.0','Accept':'application/vnd.github+json'}),timeout=25) as r:data=r.read(3000001)
   if len(data)>3000000:raise ValueError('size cap')
   name='%d.json'%number;(out/name).write_bytes(data);items=json.loads(data);manifest.append(dict(file=name,url=url,sha256=hashlib.sha256(data).hexdigest(),status='downloaded'))
   print(json.dumps(dict(number=number,files=[dict(file=x['filename'],status=x['status'],has_patch='patch' in x) for x in items])))
  except Exception as e:manifest.append(dict(url=url,status='unavailable',error=str(e)))
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print('saved',len(manifest))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
