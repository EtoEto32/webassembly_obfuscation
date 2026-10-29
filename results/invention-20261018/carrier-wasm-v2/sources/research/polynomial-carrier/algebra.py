"""Exact formal polynomials over Z/(2**32), with four state vars and one input."""
import random
MASK=(1<<32)-1
N=4


def const(x):return {():x&MASK} if x&MASK else {}
def var(i):return {(i,):1}
def add(a,b):
    c=dict(a)
    for k,v in b.items():
        c[k]=(c.get(k,0)+v)&MASK
        if not c[k]:del c[k]
    return c
def scale(a,c):return {k:(v*c)&MASK for k,v in a.items() if (v*c)&MASK}
def mul(a,b):
    c={}
    for k,v in a.items():
        for l,w in b.items():c=add(c,{tuple(sorted(k+l)):(v*w)&MASK})
    if len(c)>10000:raise ValueError('Polynomial term budget')
    return c
def substitute(a,xs):
    c={}
    for k,v in a.items():
        t=const(v)
        for i in k:t=mul(t,xs[i])
        c=add(c,t)
    return c
def dot(cs,xs):
    c={}
    for k,p in zip(cs,xs):c=add(c,scale(p,k))
    return c
def identity():return [[int(i==j) for j in range(N)] for i in range(N)]
def inverse(a):
    rows=[[(x&MASK) for x in row]+[int(i==j) for j in range(N)] for i,row in enumerate(a)]
    for j in range(N):
        pivot=next((i for i in range(j,N) if rows[i][j]&1),None)
        if pivot is None:raise ValueError('Matrix not invertible modulo 2**32')
        rows[j],rows[pivot]=rows[pivot],rows[j];inv=pow(rows[j][j],-1,1<<32)
        rows[j]=[(x*inv)&MASK for x in rows[j]]
        for i in range(N):
            if i!=j:
                c=rows[i][j];rows[i]=[(x-c*y)&MASK for x,y in zip(rows[i],rows[j])]
    return [row[N:] for row in rows]
def basis(seed):
    a=identity();rng=random.Random(seed)
    for _ in range(16):
        i,j=rng.sample(range(N),2);c=rng.randrange(1,16)
        a[i]=[(x+c*y)&MASK for x,y in zip(a[i],a[j])]
    return a
def conjugate(f,a):
    b=inverse(a);xs=[dot(row,[var(i) for i in range(N)]) for row in b]+[var(N)]
    inner=[substitute(p,xs) for p in f]
    return [dot(row,inner) for row in a],b[0]
def serial(f):return [[dict(monomial=list(k),coefficient=v) for k,v in sorted(p.items())] for p in f]
def unserial(f):return [{tuple(x['monomial']):x['coefficient'] for x in p} for p in f]


def preimage(f,target):
    """Solve sum v_i*f_i=target, using odd pivots; verify every coefficient.

    Failure is inconclusive outside this restricted solver, never a hardness
    claim. Equality of formal coefficients is sufficient, not necessary over
    this finite ring (null polynomials are possible).
    """
    terms=sorted(set(target).union(*(set(p) for p in f)))
    rows=[[p.get(k,0) for p in f]+[target.get(k,0)] for k in terms];pivotrows={};r=0
    for j in range(N):
        pivot=next((i for i in range(r,len(rows)) if rows[i][j]&1),None)
        if pivot is None:continue
        rows[r],rows[pivot]=rows[pivot],rows[r];q=pow(rows[r][j],-1,1<<32)
        rows[r]=[(x*q)&MASK for x in rows[r]]
        for i in range(len(rows)):
            if i!=r:
                c=rows[i][j];rows[i]=[(x-c*y)&MASK for x,y in zip(rows[i],rows[r])]
        pivotrows[j]=r;r+=1
    if len(pivotrows)!=N:return None,dict(status='no_full_unit_pivot',rank=len(pivotrows))
    v=[rows[pivotrows[j]][-1] for j in range(N)]
    if dot(v,f)!=target:return None,dict(status='inconsistent_formal_coefficients',rank=N)
    return v,dict(status='success',rank=N)


def observe_recover(f,c):
    rows=[c];steps=[]
    for _ in range(N-1):
        v,report=preimage(f,dot(rows[-1],[var(i) for i in range(N)]));steps.append(report)
        if v is None:return None,dict(status='inconclusive',steps=steps)
        rows.append(v)
    try:inv=inverse(rows)
    except ValueError:return None,dict(status='inconclusive',reason='dependent observables',steps=steps)
    xs=[dot(row,[var(i) for i in range(N)]) for row in inv]+[var(N)]
    result=[substitute(dot(row,f),xs) for row in rows]
    # Exact formal intertwining identity in the implemented modular ring.
    assert all(substitute(p,[dot(row,[var(i) for i in range(N)]) for row in rows]+[var(N)])==dot(row,f)
               for p,row in zip(result,rows))
    return result,dict(status='success',observations=rows,steps=steps)


def factor_recover(f,c):
    """Follow a chain Q(c*F)=(c*z)*(d*z), solving linearly for d.

    This is a known-factor polynomial division attack. It does not solve
    general polynomial isomorphism, nor assume it is hard.
    """
    rows=[c];steps=[]
    for _ in range(N-1):
        current=dot(rows[-1],[var(i) for i in range(N)])
        target={k:v for k,v in dot(rows[-1],f).items() if len(k)==2}
        products=[mul(current,var(j)) for j in range(N)]
        v,report=preimage(products,target);steps.append(report)
        if v is None:return None,dict(status='inconclusive',steps=steps)
        rows.append(v)
    try:inv=inverse(rows)
    except ValueError:return None,dict(status='inconclusive',reason='dependent factors',steps=steps)
    xs=[dot(row,[var(i) for i in range(N)]) for row in inv]+[var(N)]
    result=[substitute(dot(row,f),xs) for row in rows]
    assert all(substitute(p,[dot(row,[var(i) for i in range(N)]) for row in rows]+[var(N)])==dot(row,f)
               for p,row in zip(result,rows))
    return result,dict(status='success',observations=rows,steps=steps)
