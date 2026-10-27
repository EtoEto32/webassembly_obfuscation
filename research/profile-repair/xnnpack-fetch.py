"""Fetch fixed public source files for inspection, not package/build execution."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

COMMIT='c754a15b2bed01e80679793cbe75ebc61312430f'
PATHS=['LICENSE','src/x8-lut/gen/x8-lut-wasmpshufb-u16.c','src/configs/hardware-config.c']

def main(out):
    out.mkdir(parents=True,exist_ok=True);rows=[]
    inventory=out/'config-inventory.json'
    if not inventory.exists():
        url='https://api.github.com/repos/google/XNNPACK/contents/src/configs?ref='+COMMIT
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-Research-ReadOnly'}),timeout=30) as response:data=response.read(1024*1024+1)
        if len(data)>1024*1024:raise ValueError('inventory cap')
        inventory.write_bytes(data)
    configs=json.loads(inventory.read_text(encoding='utf8'))
    extra=[r['path'] for r in configs if 'lut' in r['name'] and r['type']=='file']
    if len(extra)>5:raise ValueError('config cap')
    for name in PATHS+extra:
        url='https://raw.githubusercontent.com/google/XNNPACK/'+COMMIT+'/'+name
        file=out/name
        if file.exists():data=file.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Wasm-Research-ReadOnly'}),timeout=30) as response:data=response.read(1024*1024+1)
            if len(data)>1024*1024:raise ValueError('file cap')
            file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
        rows.append({'path':name,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    (out/'provenance.json').write_text(json.dumps({'repository':'google/XNNPACK','commit':COMMIT,'files':rows},indent=2),encoding='utf8');print(json.dumps(rows))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();main(a.output.resolve())
