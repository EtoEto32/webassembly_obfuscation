import argparse,json
from pathlib import Path
import prototype as p
def main(data,out):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);m=json.loads((data/'manifest.json').read_text());records=[]
    for r in m['rows']:
        target=out/r['component']
        if not r['opt']:p.transform(data/r['source'],target,r['mode'],r['transform']['seed'])
        else:p.jco('opt',out/r['component'].replace('-o3','-raw'),'-o',target,'--quiet','--','-O3','--strip-debug')
        rec=out/r['recovered'];p.recover(target,rec)
        for name in (r['component'],r['recovered']):
            records.append(dict(file=name,expected=p.q.digest(data/name),actual=p.q.digest(out/name),identical=(data/name).read_bytes()==(out/name).read_bytes()))
        p.q.save(out/'records.json',records)
    p.q.save(out/'summary.json',dict(files=len(records),identical=sum(r['identical'] for r in records),all_pass=all(r['identical'] for r in records)));print(json.dumps(json.loads((out/'summary.json').read_text())))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
