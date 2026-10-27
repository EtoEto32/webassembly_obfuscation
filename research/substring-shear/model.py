"""Coefficient-level independent identities, including nonunit coefficients."""
import itertools
import json
from pathlib import Path
import random
import sys
import time
import prototype as p


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);t=time.perf_counter();rng=random.Random(20261023)
    tests=[];total=0;nonunique=0
    for n in (3,4,5):
        for bits in (0,1,8,16,24,31):
            for trial in range(24):
                ps=[]
                for i in range(n):
                    poly={(-(i%2)-1,):rng.getrandbits(32)}
                    for j,k in itertools.product(range(n),repeat=2):
                        if rng.randrange(3)==0:poly[j,k]=(rng.getrandbits(32)<<bits)&p.MASK
                    ps.append(p.add(poly))
                a=rng.randrange(1,n);other=[i for i in range(n) if i!=a];b=rng.choice(other);c=rng.choice(other);alpha=rng.getrandbits(32)
                h=p.shear(ps,a,b,c,alpha);solution=p.cubic_candidates(h,a,b,c)
                if solution is None:raise AssertionError('missed actual congruence')
                residue,modulus=solution
                if (alpha-residue)%modulus:raise AssertionError('wrong solution')
                recovered=p.shear(h,a,b,c,-residue)
                if not p.lowdegree(recovered) or p.shear(recovered,a,b,c,residue)!=h:raise AssertionError('least residue failed')
                total+=1;nonunique+=modulus<(1<<32)
                tests.append(dict(n=n,bits=bits,trial=trial,a=a,b=b,c=c,alpha=alpha,residue=residue,modulus=modulus))
    # Independent finite arithmetic check for the cubic=>quartic implication:
    # a coefficient q of X_a X_a is visible unchanged in an a,b,c cubic word.
    finite=0
    for width in range(1,7):
        mod=1<<width
        for q,delta in itertools.product(range(mod),repeat=2):
            if q*delta%mod==0 and q*delta*delta%mod!=0:raise AssertionError('annihilator implication')
            finite+=1
    r=dict(random_systems=total,nonunique_congruences=nonunique,finite_pairs=finite,mismatches=0,seconds=time.perf_counter()-t,seed=20261023)
    p.q.save(out/'summary.json',r);p.q.save(out/'cases.json',tests);print(json.dumps(r))


if __name__=='__main__':main(sys.argv[1])
