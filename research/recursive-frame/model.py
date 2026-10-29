"""Independent finite integer audit of frame transport, not whole-Wasm proof."""
import argparse,itertools,json,random
from pathlib import Path
def mat(m,v,mask):return ((m[0]*v[0]+m[1]*v[1])&mask,(m[2]*v[0]+m[3]*v[1])&mask)
def inv(m,v,mask):return ((m[3]*v[0]-m[1]*v[1])&mask,(m[0]*v[1]-m[2]*v[0])&mask)
def det(m,mask):return (m[0]*m[3]-m[1]*m[2])&mask
def shift(m,k,l,mask):
    a,b=(m[0]+k*m[2])&mask,(m[1]+k*m[3])&mask
    return (a,b,(m[2]+l*a)&mask,(m[3]+l*b)&mask)
def check(m,v,w):
    mask=(1<<w)-1;z=mat(m,v,mask);k=z[0]^z[1];l=(z[1]+3)&mask;n=shift(m,k,l,mask)
    assert det(n,mask)==1 and inv(m,z,mask)==v
    source=((v[1]+3)&mask,(v[0]^(v[1]*v[1]+1))&mask)
    child=mat(n,source,mask);assert inv(n,child,mask)==source
    out=((source[0]^5)&mask,(source[1]+7)&mask)
    transported=mat(m,out,mask);assert inv(m,transported,mask)==out
    bad=(n[0],n[1],n[2],(n[3]+1)&mask)
    return inv(bad,mat(bad,source,mask),mask)!=source
def run(path):
    path=Path(path)
    if path.exists():raise FileExistsError(path)
    rows=[]
    for w in (1,2,3):
        q=1<<w;count=0;matrices=0;bad=0
        for m in itertools.product(range(q),repeat=4):
            if det(m,q-1)!=1:continue
            matrices+=1
            for v in itertools.product(range(q),repeat=2):bad+=check(m,v,w);count+=1
        rows.append(dict(width=w,matrices=matrices,value_pairs=count,bad_mismatches=bad))
    rng=random.Random(221031);noncommute=0;bad=0
    for _ in range(10000):
        m=(1,0,0,1)
        for j in range(4):m=shift(m,rng.getrandbits(32),rng.getrandbits(32),(1<<32)-1)
        v=(rng.getrandbits(32),rng.getrandbits(32));bad+=check(m,v,32)
        k,l=rng.getrandbits(32),rng.getrandbits(32)
        noncommute+=shift(m,k,l,(1<<32)-1)!=shift(shift(m,0,l,(1<<32)-1),k,0,(1<<32)-1)
    path.parent.mkdir(parents=True,exist_ok=True)
    result=dict(exhaustive=rows,random32_cases=10000,random32_bad_mismatches=bad,noncommuting_order_cases=noncommute,seed=221031,scope='single transport identity; not entire recursive Wasm or all input proof')
    path.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
