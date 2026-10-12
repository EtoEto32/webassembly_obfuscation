import hashlib
import json
import os
import platform
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, os.environ.get('RESIDUAL_CAS', str(ROOT.parents[1]/'.tools'/'nonbijective-residual-cas')))
import sympy as sp
from factor_observer import recover


def q(a,b,modulus):
    return ((a+a*(a+1)*b)%modulus, (b+b*(b+1)*a)%modulus)


def main():
    if (ROOT/'results.json').exists():
        raise RuntimeError('Preserve existing results')
    residuals=[]
    for width in range(1,9):
        m=1<<width
        zeros=[]
        images=set()
        for a in range(m):
            for b in range(m):
                value=q(a,b,m)
                images.add(value)
                if value==(0,0): zeros.append([a,b])
        residuals.append(dict(width=width,pairs=m*m,zeros=zeros,image_size=len(images)))
        assert zeros==[[0,0]]
    collisions=[]
    for width in range(2,33):
        first=q(1,0,1<<width); second=q(1,1<<(width-1),1<<width)
        assert first==second
        collisions.append(dict(width=width,first=[1,0],second=[1,1<<(width-1)],image=first))

    x,y,z,t=sp.symbols('x y z t')
    variables=[x,y,z,t]
    rng=random.Random(0x4E4F4E42)
    observations=[]; rows=[]
    for group in ['small','large']:
        for instance in range(4):
            c=[rng.randint(1,7) if group=='small' else rng.getrandbits(32) for _ in range(4)]
            f=x*x+c[0]*x*y+c[1]*y
            g=y*y+c[2]*x+c[3]*x*y
            a,b=z-f,t-g
            expressions=[a+a*(a+1)*b,b+b*(b+1)*a]
            equations=[]
            for expression in expressions:
                poly=sp.Poly(sp.expand(expression),*variables)
                equations.append([[list(e), int((int(v)+(1<<31))%(1<<32)-(1<<31))]
                                  for e,v in poly.terms()])
            payload=dict(width=32,variables=[str(v) for v in variables],equations=equations)
            found=recover(payload)
            success=[]
            for wanted,out,candidates in zip([f,g],['z','t'],found):
                match=False
                for name,expression in candidates:
                    difference=sp.Poly(sp.expand(expression-wanted),x,y)
                    if name==out and all(int(v)%(1<<32)==0 for v in difference.coeffs()):
                        match=True
                success.append(match)
            observations.append(payload)
            rows.append(dict(group=group,instance=instance,source_coefficients=c,
                             source=[str(f),str(g)],recovered=[[(n,str(e)) for n,e in p] for p in found],
                             exact_source_relations=success))
    (ROOT/'observations.json').write_text(json.dumps(observations),encoding='utf-8')
    result=dict(python=platform.python_version(),sympy=sp.__version__,seed=0x4E4F4E42,
                residuals=residuals,collisions=collisions,factorization=rows,
                hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                        for name in ['check.py','factor_observer.py','protocol.md','observations.json']})
    (ROOT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(residual_pairs=sum(r['pairs'] for r in residuals),
                         collision_widths=len(collisions),
                         factorization=[dict(group=g,success=sum(all(r['exact_source_relations']) for r in rows if r['group']==g),cases=4) for g in ['small','large']])) )


if __name__=='__main__': main()
