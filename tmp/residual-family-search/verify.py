import hashlib
import itertools
import json
import os
from pathlib import Path
import sys
import search

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,os.environ['RESIDUAL_CAS_PATH'])
import sympy as sp

def main():
    destination=ROOT/'verification.json'
    if destination.exists(): raise RuntimeError('Preserve existing verification')
    # Independent exhaustive check of solver decisions over a smaller ring.
    search.WIDTH=2; search.MOD=4
    checks=0
    for entries in itertools.product(range(4),repeat=4):
        matrix=[entries[:2],entries[2:]]
        attainable={tuple(sum(x*y for x,y in zip(row,vector))%4 for row in matrix)
                    for vector in itertools.product(range(4),repeat=2)}
        for target in itertools.product(range(4),repeat=2):
            result=search.solve(matrix,target)
            assert (result is not None)==(target in attainable)
            checks+=1
    search.WIDTH=32; search.MOD=1<<32
    saved=json.loads((ROOT/'results.json').read_text())
    F,G,z,t=sp.symbols('F G z t')
    a,b=z-F,t-G
    records=[]
    for row in saved['cases']:
        r=[sum(c*a**i*b**j for (i,j),c in row[name]) for name in ['r1','r2']]
        q=[sp.Poly(sp.expand(a+a*(a+1)*b*r[0]),z,t),
           sp.Poly(sp.expand(b+b*(b+1)*a*r[1]),z,t)]
        verified=[]
        for wanted,witness in zip([F,G],row['coefficient_recovery']):
            if witness is None:
                verified.append(None); continue
            expression=0
            for (index,i,j),c in witness:
                expression+=c*(1 if index=='constant' else q[index].coeff_monomial(z**i*t**j))
            coefficients=sp.Poly(sp.expand(expression-wanted),F,G).coeffs()
            assert all(int(c)%(1<<32)==0 for c in coefficients)
            verified.append(True)
        records.append(dict(degree_bound=row['degree_bound'],instance=row['instance'],verified=verified))
    result=dict(sympy=sp.__version__,solver_small_ring_cases=checks,cases=records,
        source_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                       for name in ['search.py','verify.py','results.json']})
    destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(solver_cases=checks,positive_witnesses=sum(x is True for r in records for x in r['verified']))))

if __name__=='__main__': main()
