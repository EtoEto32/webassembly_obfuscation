"""Bounded algebraic candidate search. Standard library only, no Wasm claim."""
import hashlib
import json
import platform
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 0x52455349
WIDTH = 32
MOD = 1 << WIDTH
ZERO = (0, 0, 0, 0)  # Formal unknown F,G and outputs z,t.

def const(c):
    return {ZERO: c % MOD} if c % MOD else {}

def add(*polys):
    out = {}
    for p in polys:
        for e,c in p.items():
            out[e] = (out.get(e,0)+c) % MOD
    return {e:c for e,c in out.items() if c}

def mul(p,q):
    out = {}
    for e,c in p.items():
        for f,d in q.items():
            k=tuple(x+y for x,y in zip(e,f))
            out[k]=(out.get(k,0)+c*d) % MOD
    return {e:c for e,c in out.items() if c}

def power(p,n):
    out=const(1)
    for _ in range(n): out=mul(out,p)
    return out

def v2(x):
    return (x & -x).bit_length()-1 if x else WIDTH

def solve(matrix, target):
    """Solve A*x=b modulo 2^WIDTH using minimum-valuation pivots."""
    a=[list(row)+[b] for row,b in zip(matrix,target)]
    nr,nc=len(a),len(matrix[0])
    order=list(range(nc)); rank=0
    while rank < min(nr,nc):
        candidates=[(v2(a[i][j]),i,j) for i in range(rank,nr)
                    for j in range(rank,nc) if a[i][j]]
        if not candidates: break
        valuation,i,j=min(candidates)
        a[rank],a[i]=a[i],a[rank]
        for row in a: row[rank],row[j]=row[j],row[rank]
        order[rank],order[j]=order[j],order[rank]
        odd=a[rank][rank] >> valuation
        inv=pow(odd,-1,MOD)
        a[rank]=[(entry*inv)%MOD for entry in a[rank]]
        pivot=1 << valuation
        for i in range(rank+1,nr):
            assert a[i][rank] % pivot == 0
            factor=a[i][rank]//pivot
            a[i]=[(x-factor*y)%MOD for x,y in zip(a[i],a[rank])]
        rank+=1
    if any(row[nc] for row in a[rank:]): return None
    solution=[0]*nc
    for i in range(rank-1,-1,-1):
        numerator=(a[i][nc]-sum(a[i][j]*solution[j] for j in range(i+1,nc)))%MOD
        pivot=a[i][i]
        if numerator % pivot: return None
        solution[i]=numerator//pivot
    result=[0]*nc
    for i,j in enumerate(order): result[j]=solution[i]
    assert all(sum(x*y for x,y in zip(row,result))%MOD == b%MOD for row,b in zip(matrix,target))
    return result

def evaluate_r(coeffs,a,b,modulus):
    return sum(c*pow(a,i,modulus)*pow(b,j,modulus) for (i,j),c in coeffs.items())%modulus

def residual(coeff1,coeff2,a,b,modulus):
    return ((a+a*(a+1)*b*evaluate_r(coeff1,a,b,modulus))%modulus,
            (b+b*(b+1)*a*evaluate_r(coeff2,a,b,modulus))%modulus)

def main():
    destination=ROOT/'results.json'
    if destination.exists(): raise RuntimeError('Preserve existing results')
    rng=random.Random(SEED)
    a={(0,0,1,0):1,(1,0,0,0):MOD-1}
    b={(0,0,0,1):1,(0,1,0,0):MOD-1}
    records=[]
    for degree in [0,1,2]:
        for instance in range(32):
            exps=[(i,j) for i in range(degree+1) for j in range(degree+1-i)]
            r1={e:rng.randrange(16) for e in exps}
            r2={e:rng.randrange(16) for e in exps}
            # Guarantees R2(1,0) odd, hence the stated collision for every w>=2.
            if sum(c for (i,j),c in r2.items() if j==0)%2==0: r2[(0,0)]^=1
            def lift(r):
                return add(*(mul(const(c),mul(power(a,i),power(b,j))) for (i,j),c in r.items()))
            q1=add(a,mul(mul(mul(a,add(a,const(1))),b),lift(r1)))
            q2=add(b,mul(mul(mul(b,add(b,const(1))),a),lift(r2)))
            # Each column is one output-monomial coefficient in R[F,G].
            columns=[{(0,0):1}]; labels=[['constant',0,0]]
            for index,q in enumerate([q1,q2]):
                grouped={}
                for (i,j,k,l),c in q.items():
                    grouped.setdefault((k,l),{})[(i,j)]=c
                for output_exp,poly in sorted(grouped.items()):
                    columns.append(poly); labels.append([index,*output_exp])
            monomials=sorted(set().union(*[set(p) for p in columns],{(1,0),(0,1)}))
            matrix=[[p.get(e,0) for p in columns] for e in monomials]
            witnesses=[]
            for wanted in [(1,0),(0,1)]:
                solution=solve(matrix,[int(e==wanted) for e in monomials])
                witnesses.append(None if solution is None else [[label,c] for label,c in zip(labels,solution) if c])
            zeros=[(x,y) for x in range(8) for y in range(8) if residual(r1,r2,x,y,8)==(0,0)]
            assert zeros==[(0,0)]
            collisions=[]
            for width in [2,3,8,16,32]:
                first=residual(r1,r2,1,0,1<<width)
                second=residual(r1,r2,1,1<<(width-1),1<<width)
                assert first==second
                collisions.append(dict(width=width,image=first))
            records.append(dict(degree_bound=degree,instance=instance,
                r1=[[list(e),c] for e,c in sorted(r1.items())],
                r2=[[list(e),c] for e,c in sorted(r2.items())],
                coefficient_recovery=witnesses,small_width_zero_pairs=64,collisions=collisions))
    result=dict(python=platform.python_version(),seed=SEED,width=WIDTH,cases=records,
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps([dict(degree=d,cases=32,both_recovered=sum(all(x is not None for x in r['coefficient_recovery']) for r in records if r['degree_bound']==d),
         neither_recovered=sum(all(x is None for x in r['coefficient_recovery']) for r in records if r['degree_bound']==d)) for d in [0,1,2]]))

if __name__=='__main__': main()
