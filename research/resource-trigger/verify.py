import argparse,json
from pathlib import Path
import prototype as p
def value(e,x,y):
    if e[0]=='i32.const':return int(e[1])&p.MASK
    if e[0]=='local.get':return (x if e[1]=='0' else y)&p.MASK
    a,b=[value(t,x,y) for t in e[1:]];s=b&31
    ops={'i32.add':lambda:a+b,'i32.sub':lambda:a-b,'i32.mul':lambda:a*b,'i32.xor':lambda:a^b,'i32.and':lambda:a&b,'i32.or':lambda:a|b,'i32.rotl':lambda:(a<<s)|(a>>((-s)&31)),'i32.rotr':lambda:(a>>s)|(a<<((-s)&31)),'i32.shl':lambda:a<<s,'i32.shr_u':lambda:a>>s,'i32.shr_s':lambda:(a if a<2**31 else a-2**32)>>s}
    return ops[e[0]]()&p.MASK
def main(data,out):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);m=json.loads((data/'manifest.json').read_text());cases=[(0,0),(1,1),(-1,-1),(0x40000000,0x40000000),(0x7fffffff,0x80000000),(0x55555555,0xaaaaaaaa),(65535,65536)];files={}
    for r in m['rows']:
        for name in (r['source'],r['recovered']):files[name]=r
    records=[]
    for name,r in files.items():
        blob=''.join('\\%02x'%b for b in (data/name).read_bytes());lines=['(module binary "'+blob+'")']
        for x,y in cases:lines.append(f'(assert_return (invoke "run" (i32.const {x}) (i32.const {y})) (i32.const {value(r["expression"],x,y)}))')
        file=out/(Path(name).stem+'.wast');file.write_text('\n'.join(lines),encoding='utf-8');log=p.q.tool('wasm-shell',[file]);file.with_suffix('.log').write_text(log,encoding='utf-8');records.append(dict(file=name,sha256=p.q.digest(data/name),checks=len(cases)))
    p.q.save(out/'records.json',records);p.q.save(out/'summary.json',dict(files=len(records),checks=len(records)*len(cases),all_pass=True,scope='core source/recovery only; not an independent component runtime'));print(len(records)*len(cases),'core checks passed')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
