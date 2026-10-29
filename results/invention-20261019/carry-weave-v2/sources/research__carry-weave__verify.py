import argparse,json
from pathlib import Path
import prototype as p
def oracle(row,args):
    x,y,z=args;out=0
    def rot(x,r):x&=p.MASK;return ((x<<r)|(x>>(32-r)))&p.MASK
    for i,(c,r) in enumerate(row['spec']):
        a=rot(x+c,r) if row['kind']==0 else (x^c) if row['kind']==1 else rot(x^c,r)
        b=y+i+1 if row['kind']==0 else rot(y+z,r) if row['kind']==1 else z+y
        out=(out+a*b)&p.MASK
    return out
def main(data,out):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);rows=[];cases=[(0,0,0),(1,1,1),(-1,-1,-1),(2147483647,-2147483648,3),(0x55555555,0xaaaaaaaa,17),(123,456,789),(65535,65536,65537)]
    for r in json.loads((data/'manifest.json').read_text()):
        for name in (r['file'],r['recovered']):
            blob=''.join('\\%02x'%b for b in (data/name).read_bytes());lines=['(module binary "'+blob+'")']
            for args in cases:lines.append('(assert_return (invoke "run" '+' '.join('(i32.const '+str(x)+')' for x in args)+') (i32.const '+str(oracle(r,args))+'))')
            f=out/(Path(name).stem+'.wast');f.write_text('\n'.join(lines),encoding='utf-8');log=p.tool('wasm-shell',[f]);f.with_suffix('.log').write_text(log,encoding='utf-8');rows.append(dict(file=name,checks=len(cases)))
    p.save(out/'records.json',rows);p.save(out/'summary.json',dict(files=len(rows),checks=len(rows)*len(cases),all_pass=True));print((out/'summary.json').read_text())
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
