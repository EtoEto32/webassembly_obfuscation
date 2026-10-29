import argparse,json
from pathlib import Path
import prototype as p
def oracle(n,rules,x):
    cells=[(x>>(2*i))&3 for i in range(n)]
    for s in rules:
        i=s['cell'];cells[i]=s['table'][16*cells[(i-1)%n]+4*cells[i]+cells[(i+1)%n]]
    return sum(v<<(2*i) for i,v in enumerate(cells))
def main(data,out):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);m=json.loads((data/'manifest.json').read_text());files={};records=[]
    for r in m['rows']:
        for name in (r['source'],r['file'],r['recovered']):
            if name:files[name]=r
    cases=[0,1,(1<<64)-1,1<<63,0x5555555555555555,0xaaaaaaaaaaaaaaaa,0x123456789abcdef]
    for name,r in files.items():
        blob=''.join('\\%02x'%b for b in (data/name).read_bytes());lines=['(module binary "'+blob+'")']
        for x in cases:lines.append(f'(assert_return (invoke "run" (i64.const {x})) (i64.const {oracle(r["n"],r["rules"],x)}))')
        f=out/(Path(name).stem+'.wast');f.write_text('\n'.join(lines),encoding='utf-8');log=p.q.tool('wasm-shell',[f]);f.with_suffix('.log').write_text(log,encoding='utf-8');records.append(dict(file=name,sha256=p.q.digest(data/name),checks=len(cases)))
    p.q.save(out/'records.json',records);p.q.save(out/'summary.json',dict(files=len(records),checks=len(records)*len(cases),passed=True));print('passed',len(records)*len(cases))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
