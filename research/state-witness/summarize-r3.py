"""Recompute the original three-condition, two-engine R3 summary."""
import argparse,hashlib,json,shutil
from pathlib import Path
def main(node,first,retry,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for entry in json.loads((node/'results.json').read_text())['rows']:
        name=entry['name'];a=json.loads((node/(name+'.json')).read_text())
        source=retry/(name+'.json') if (retry/(name+'.json')).exists() else first/(name+'.json')
        b=json.loads(source.read_text());assert len(a['rows'])==len(b['rows'])==3
        assert all(x['outcome']==y['outcome'] for x,y in zip(a['rows'],b['rows']))
        match=all(x['memorySha256']==y['memorySha256'] for x,y in zip(a['rows'],b['rows']));assert match
        rows.append({'name':name,'nodeOutcome':a['rows'][0]['outcome'],'wasmtimeOutcome':b['rows'][0]['outcome'],
          'nodeStatuses':[x['status'] for x in a['rows']],'wasmtimeStatuses':[x['status'] for x in b['rows']],
          'memoryBytes':a['rows'][0]['memoryBytes'],'crossEngineMemoryHashesMatch':match,'wasmtimeSource':str(source)})
    r={'rows':rows,'normalModules':sum(not x['nodeOutcome'].get('trap') for x in rows),'matchingTrapModules':sum(bool(x['nodeOutcome'].get('trap')) for x in rows),
       'scope':'Exact bytes were compared within each engine; cross-engine comparison uses SHA-256, not a byte-for-byte proof.'}
    (out/'results.json').write_text(json.dumps(r,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in r.items() if isinstance(v,int)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('node',type=Path);p.add_argument('first',type=Path);p.add_argument('retry',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.node,v.first,v.retry,v.out)
