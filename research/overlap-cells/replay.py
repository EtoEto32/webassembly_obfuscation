import argparse,json
from pathlib import Path
import prototype as p

def main(data,out):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);m=json.loads((data/'manifest.json').read_text());records=[]
    def compare(name):
        expected=p.q.digest(data/name);actual=p.q.digest(out/name);records.append(dict(file=name,expected=expected,actual=actual,identical=expected==actual));p.q.save(out/'records.json',records)
    for n,family in sorted({(r['n'],r['family']) for r in m['rows']}):
        rows=[r for r in m['rows'] if r['n']==n and r['family']==family];r=rows[0];src=out/r['source'];p.q.compile(p.fixture(n,r['rounds'],family),src);compare(src.name);p.plain_canonical(src,out/r['canonical']);compare(r['canonical'])
        for r in rows:
            target=out/r['file']
            if not r['opt']:p.transform(src,target,r['mode'],r['transform']['seed'])
            else:p.q.tool('wasm-opt',[out/r['file'].replace('-o3','-raw'),'-O3','--strip-debug','-o',target]);p.w.tool('wasm-validate',[target])
            compare(target.name)
            if r['recovered']:p.recover(target,out/r['recovered']);compare(r['recovered'])
    summary=dict(files=len(records),identical=all(r['identical'] for r in records));p.q.save(out/'summary.json',summary);print(summary)
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
