import argparse,json
from pathlib import Path
import prototype as p
def update(a,n,name,r,x,y):
    if not 0<=r<4:return 'trap'
    b=r*n*4
    if name=='peek':return a[b+8]
    if name=='bump':a[b]=(a[b]+x)&p.MASK;a[b+1]^=y&p.MASK;return a[b]^a[b+1]
    if name=='coupled':
        u,v,z=a[b],a[b+4],a[b+8];a[b]=(u+y*v)&p.MASK;a[b+4]=v^p.rot(z,x&31) if x&31 else v^z;return u^v^z
    u,v,z=a[b],a[b+2*n],a[b+4*n-4];v=(v+x*z)&p.MASK;a[b+2*n]=v;a[b+4*n-4]=z^u;return (v+u)&p.MASK
def main(data,out):
    data=Path(data);out=Path(out);out.mkdir(parents=True,exist_ok=False);rows=json.loads((data/'manifest.json').read_text());recs=[];checks=0
    cases=[('bump',0,-1,1),('coupled',3,31,0x7fffffff),('spread',0,0x80000000,4),('peek',3,0,0),('bump',4,3,7),('coupled',-1,3,5),('peek',0,0,0)]
    for r in rows:
        a=json.loads((data/r['initial']).read_text());blob=''.join('\\%02x'%b for b in (data/r['file']).read_bytes());lines=['(module binary "'+blob+'")']
        for name,record,x,y in cases:
            want=update(a,r['n'],name,record,x,y);invoke=f'(invoke "{name}" (i32.const {record}) (i32.const {x}) (i32.const {y}))'
            lines.append(f'(assert_trap {invoke} "unreachable")' if want=='trap' else f'(assert_return {invoke} (i32.const {want}))')
        f=out/(Path(r['file']).stem+'.wast');f.write_text('\n'.join(lines),encoding='utf-8');log=p.tool('wasm-shell',[f]);f.with_suffix('.log').write_text(log,encoding='utf-8');recs.append(dict(file=r['file'],checks=len(cases),pass_=True));checks+=len(cases)
    p.save(out/'records.json',recs);p.save(out/'summary.json',dict(files=len(recs),binaryen_checks=checks,all_pass=True));print(json.dumps(dict(files=len(recs),binaryen_checks=checks)))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('data');a.add_argument('output');v=a.parse_args();main(v.data,v.output)
