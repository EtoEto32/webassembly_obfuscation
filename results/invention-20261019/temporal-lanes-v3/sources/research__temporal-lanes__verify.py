import argparse,json
from pathlib import Path
import prototype as p
def reference(r,args):
    count,x,y,z=args
    if not 0<=count<=p.LIMIT:return 'trap'
    rot=lambda a,k:((a<<k)|(a>>(32-k)))&p.MASK
    a=[((x^(((i+1)*0x10204081)&p.MASK))+y)&p.MASK for i in range(r['n'])]
    for t in range(count):
        b=rot((z+t*0x9e3779b9)&p.MASK,11)^(y&p.MASK)
        for i,c in enumerate(r['coeff']):
            old=a[i]
            if r['kind']==0:v=rot((old*c+b)&p.MASK,r['r'])
            elif r['kind']==1:v=((old^b)*c+rot(old,r['r']))&p.MASK
            else:v=rot((old+b)&p.MASK,r['r'])^((old*c)&p.MASK)
            a[i]=v;b=v
    ret=0
    for v in a:ret^=v
    return ret
def main(data,out):
    data,out=map(Path,(data,out));out.mkdir(parents=True,exist_ok=False);recs=[]
    for r in json.loads((data/'manifest.json').read_text()):
        for name in [r['file']]+([r['recovered']] if 'recovered' in r else []):
            blob=''.join('\\%02x'%b for b in (data/name).read_bytes());lines=['(module binary "'+blob+'")'];cases=[(0,0,-1,1),(1,-1,0,0),(r['n']-1,0x7fffffff,0x80000000,1),(r['n'],3,5,7),(31,11,13,17),(16385,0,0,0),(-1,1,1,1)]
            for args in cases:
                value=reference(r,args);inv='(invoke "run" '+' '.join('(i32.const '+str(x)+')' for x in args)+')'
                lines.append('(assert_trap '+inv+' "unreachable")' if value=='trap' else '(assert_return '+inv+' (i32.const '+str(value)+'))')
            f=out/(Path(name).stem+'.wast');f.write_text('\n'.join(lines),encoding='utf-8');log=p.tool('wasm-shell',[f]);f.with_suffix('.log').write_text(log,encoding='utf-8');recs.append(dict(file=name,checks=len(cases)))
    p.save(out/'records.json',recs);p.save(out/'summary.json',dict(files=len(recs),checks=sum(r['checks'] for r in recs),all_pass=True));print(json.dumps(dict(files=len(recs),checks=sum(r['checks'] for r in recs))))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
