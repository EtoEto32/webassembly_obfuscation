"""Record bounded primary-source issue searches; search hits are not verified bugs."""
import argparse,hashlib,json,urllib.request,urllib.parse
from pathlib import Path
QUERIES=['repo:WebAssembly/binaryen is:pr is:merged struct fix','repo:WebAssembly/binaryen is:pr is:merged "ref.eq"','repo:WebAssembly/binaryen is:issue miscompilation']
def main(out):
 out.mkdir(parents=True,exist_ok=False);manifest=[]
 for i,q in enumerate(QUERIES):
  url='https://api.github.com/search/issues?'+urllib.parse.urlencode(dict(q=q,sort='updated',order='desc',per_page=15))
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-local-research/1.0','Accept':'application/vnd.github+json'}),timeout=25) as r:data=r.read(3000001)
   if len(data)>3000000:raise ValueError('size cap')
   name='%d.json'%i;(out/name).write_bytes(data);items=json.loads(data);manifest.append(dict(file=name,query=q,url=url,sha256=hashlib.sha256(data).hexdigest(),total=items.get('total_count'),status='downloaded'))
   print(json.dumps(dict(query=q,total=items.get('total_count'),items=[dict(number=x['number'],title=x['title'],url=x['html_url'],created=x['created_at']) for x in items.get('items',[])]),ensure_ascii=False))
  except Exception as e:manifest.append(dict(query=q,url=url,status='unavailable',error=str(e)))
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
