import argparse,hashlib,json,urllib.request
from pathlib import Path
URLS={
 'dumpling.pdf':'https://www.ndss-symposium.org/wp-content/uploads/2025-1411-paper.pdf',
 'fuzzjit.pdf':'https://www.usenix.org/system/files/usenixsecurity23-wang-junjie.pdf',
 'js-api.html':'https://webassembly.github.io/spec/js-api/',
 'java-serialization.html':'https://docs.oracle.com/en/java/javase/25/docs/specs/serialization/serial-arch.html',
}
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
 ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
