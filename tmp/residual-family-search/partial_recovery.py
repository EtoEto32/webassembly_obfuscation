"""Check whether nonunit coefficient witnesses leave only a small root search."""
import json
import os
from pathlib import Path
import random
import sys
import search
sys.path.insert(0,os.environ['RESIDUAL_CAS_PATH'])
import sympy as sp
ROOT=Path(__file__).resolve().parent
MOD=1<<32

def evaluate(poly,values):
    return sum(c*pow(values[0],e[0],MOD)*pow(values[1],e[1],MOD) for e,c in poly.items())%MOD

def main():
    destination=ROOT/'partial-results.json'
    if destination.exists(): raise RuntimeError('Preserve existing results')
    rng=random.Random(0x50415254)
    F,G,z,t=sp.symbols('F G z t'); a,b=z-F,t-G
    rows=[]
    for saved in json.loads((ROOT/'results.json').read_text())['cases']:
        r=[sum(c*a**i*b**j for (i,j),c in saved[name]) for name in ['r1','r2']]
        q=[sp.Poly(sp.expand(a+a*(a+1)*b*r[0]),z,t),sp.Poly(sp.expand(b+b*(b+1)*a*r[1]),z,t)]
        columns=[{(0,0):1}]; labels=[['constant',0,0]]
        for index,p in enumerate(q):
            for (i,j),coefficient in p.terms():
                columns.append({e:int(c)%MOD for e,c in sp.Poly(coefficient,F,G).terms() if int(c)%MOD})
                labels.append([index,i,j])
        monomials=sorted(set().union(*[set(p) for p in columns],{(1,0),(0,1)}))
        matrix=[[p.get(e,0) for p in columns] for e in monomials]
        witnesses=[]; shifts=[]
        for wanted in [(1,0),(0,1)]:
            for shift in range(33):
                target=[(1<<shift)%MOD if e==wanted else 0 for e in monomials]
                found=search.solve(matrix,target)
                if found is not None: break
            shifts.append(shift); witnesses.append(found)
        samples=[]
        if sum(shifts)<=8:
            for _ in range(16):
                expected=[rng.getrandbits(32),rng.getrandbits(32)]
                # Verifier creates only public equation coefficients for the observer.
                public=[evaluate(p,expected) for p in columns]
                lows=[(sum(c*v for c,v in zip(w,public))%MOD)>>s for w,s in zip(witnesses,shifts)]
                observed=[]
                for i in range(1<<shifts[0]):
                    for j in range(1<<shifts[1]):
                        point=[lows[0]+(i<<(32-shifts[0])),lows[1]+(j<<(32-shifts[1]))]
                        values=[0,0]
                        for label,value in zip(labels[1:],public[1:]):
                            index,k,l=label
                            values[index]=(values[index]+value*pow(point[0],k,MOD)*pow(point[1],l,MOD))%MOD
                        if values==[0,0]: observed.append(point)
                assert observed==[expected]
                samples.append(dict(expected=expected,recovered=observed[0]))
        rows.append(dict(degree_bound=saved['degree_bound'],instance=saved['instance'],missing_bits=shifts,
                         witnesses=[[[label,c] for label,c in zip(labels,w) if c] for w in witnesses],samples=samples))
    destination.write_text(json.dumps(dict(seed=0x50415254,max_candidate_bits=8,cases=rows),indent=2),encoding='utf-8')
    print(json.dumps(dict(cases=len(rows),max_missing_bits=max(sum(r['missing_bits']) for r in rows),
                         tested_cases=sum(bool(r['samples']) for r in rows),
                         verified_roots=sum(len(r['samples']) for r in rows),
                         survivors=[dict(degree=r['degree_bound'],instance=r['instance'],missing_bits=r['missing_bits']) for r in rows if not r['samples']])) )

if __name__=='__main__': main()
