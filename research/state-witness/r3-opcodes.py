"""Record original replay opcode counts; no dynamic execution."""
import argparse,collections,hashlib,json,shutil
from pathlib import Path
import prototype as k
def count(x,c):
    if isinstance(x,list):
        if x and isinstance(x[0],str):c[x[0]]+=1
        for y in x:count(y,c)
def main(source,audit,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for row in json.loads((audit/'results.json').read_text())['rows']:
        if row['status']!='accepted':continue
        src=next(source.rglob(row['file']));m=k.p.read(src);c=collections.Counter()
        for f in k.p.section(m,'func'):count(f,c)
        rows.append({'file':row['file'],'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
          'opcodes':{op:c[op] for op in ['memory.init','data.drop','table.init','elem.drop']}})
    (out/'results.json').write_text(json.dumps({'rows':rows},indent=2))
    shutil.copy2(__file__,out/'r3-opcodes.py')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(rows))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('audit',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.audit,v.out)
