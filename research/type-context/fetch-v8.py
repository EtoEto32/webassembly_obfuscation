"""Read the exact Git blob listed by the already saved V8 inventory."""
import argparse,base64,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main(out):
 out.mkdir(parents=True,exist_ok=False)
 listing=json.loads((ROOT/'results/type-context/more-priors-v2/v8-wasm-directory.json').read_text())
 item=next(x for x in listing if x['name']=='runtime-type-canonicalization.js')
 url=item['git_url'];row=dict(file=item['name'],url=url,git_blob=item['sha'])
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research/1.0'}),timeout=25) as r:payload=r.read(1000001)
  if len(payload)>1000000:raise ValueError('size cap')
  obj=json.loads(payload);data=base64.b64decode(obj['content'])
  assert hashlib.sha1(('blob %d\0'%len(data)).encode()+data).hexdigest()==item['sha']
  (out/item['name']).write_bytes(data);row.update(status='downloaded',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 except Exception as e:row.update(status='unavailable',error=str(e))
 (out/'manifest.json').write_text(json.dumps([row],indent=2));print(json.dumps(row,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
