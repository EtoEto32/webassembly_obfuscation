"""Recompute the mapping of concrete, static and finite-model classifications."""
import argparse,hashlib,json,shutil
from pathlib import Path
def main(source,closure,out):
    out.mkdir(parents=True,exist_ok=False);a=json.loads((source/'results.json').read_text());b=json.loads((closure/'results.json').read_text())
    key=lambda r:(r['source'],r['segment']['kind'],r['segment']['index'])
    bb={key(r):r for r in b['rows']};rows=[]
    for r in a['rows']:
        rows.append({'source':r['source'],'sha256':r['sourceSha256'],'segment':r['segment'],'defUse':r['certificate']['status'],
          'originalTrace':r['status'],'finiteModel':bb[key(r)]['result']['status']})
    result={'inputHashes':{p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (source/'results.json',closure/'results.json')},'rows':rows}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({'rows':len(rows)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('closure',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.closure,v.out)
