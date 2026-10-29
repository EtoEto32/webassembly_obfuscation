"""GF(2) centralizer construction; no secrecy or novelty claim for linear algebra."""
import random

def ident(n): return [1 << i for i in range(n)]
def bits(x):
    while x:
        t=x&-x;yield t.bit_length()-1;x^=t
def product(a,b):
    out=[]
    for row in a:
        v=0
        for k in bits(row):v^=b[k]
        out.append(v)
    return out
def inverse(a):
    n=len(a);a=[r|(1<<(n+i)) for i,r in enumerate(a)]
    for c in range(n):
        pivot=next((i for i in range(c,n) if (a[i]>>c)&1),None)
        if pivot is None:return None
        a[c],a[pivot]=a[pivot],a[c]
        for i in range(n):
            if i!=c and ((a[i]>>c)&1):a[i]^=a[c]
    return [x>>n for x in a]
def apply(a,x):
    out=[]
    for row in a:
        v=0
        for k in bits(row):v^=x[k]
        out.append(v)
    return bytes(out)
def copy_map(n,op):
    d,s,l=op
    if min(d,s,l)<0 or max(d+l,s+l)>n:raise ValueError('copy outside window')
    f=list(range(n));f[d:d+l]=range(s,s+l)
    return f
def matrix(n,op):return [1<<x for x in copy_map(n,op)]
def nullspace(eqs,nvars):
    piv={}
    for row in eqs:
        while row:
            k=row.bit_length()-1
            if k not in piv:piv[k]=row;break
            row^=piv[k]
    basis=[]
    for free in range(nvars):
        if free in piv:continue
        v=1<<free
        for k in sorted(piv):
            if bin(piv[k]&v).count('1')%2:v^=1<<k
        basis.append(v)
    return basis
def centralizer(n,ops):
    equations=[]
    for op in ops:
        f=copy_map(n,op)
        pre=[[k for k in range(n) if f[k]==j] for j in range(n)]
        for i in range(n):
            for j in range(n):
                row=1<<(f[i]*n+j)
                for k in pre[j]:row^=1<<(i*n+k)
                equations.append(row)
    return nullspace(equations,n*n)
def choose(n,ops,seed=211041):
    basis=centralizer(n,ops);rng=random.Random(seed);best=ident(n);score=0;accepted=0
    for _ in range(256):
        v=0
        for b in basis:
            if rng.randrange(2):v^=b
        rows=[(v>>(i*n))&((1<<n)-1) for i in range(n)]
        if inverse(rows) is None:continue
        accepted+=1;s=sum(bin(row).count('1') for row in rows)
        if s>score:best,score=rows,s
    for op in ops:assert product(best,matrix(n,op))==product(matrix(n,op),best)
    assert product(best,inverse(best))==ident(n)
    return best,dict(dimension=len(basis),sampled=256,invertible_samples=accepted,nonzeros=sum(bin(r).count('1') for r in best),mixed_rows=sum(bin(r).count('1')>1 for r in best))

FIXTURES={
 'blocks16':(16,[(4,0,4),(8,4,4),(0,12,4),(12,8,4),(0,4,4)]),
 'overlap8':(8,[(2,0,4),(0,2,4),(6,0,2),(0,6,2)]),
 'irregular8':(8,[(3,0,3),(6,4,2),(0,1,2)]),
 'allcells8':(8,[(d,s,1) for d in range(8) for s in range(8) if d!=s]),
}
if __name__=='__main__':
    import json
    print(json.dumps({k:choose(n,ops)[1] for k,(n,ops) in FIXTURES.items()},indent=2))
