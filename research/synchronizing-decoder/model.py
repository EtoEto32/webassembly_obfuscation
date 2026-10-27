"""Construct deterministic weighted reset words, using exact integer nullspaces."""
from fractions import Fraction
import math, random
MASK=(1<<32)-1

def automaton(n):
    if n<2 or n%2:raise ValueError('even state count required')
    transition=[[(q+1)%n for q in range(n)],[0 if q==n-1 else q for q in range(n)]]
    word=[1]+([0]*(n-1)+[1])*(n-2)
    rows=[]
    for start in range(n):
        q=start;row=[0]*(2*n)
        for a in word:row[a*n+q]+=1;q=transition[a][q]
        assert q==0;rows.append(row)
    return transition,word,rows

def kernel(matrix):
    a=[[Fraction(v) for v in row] for row in matrix];r=0;pivots=[];cols=len(a[0])
    for c in range(cols):
        at=next((i for i in range(r,len(a)) if a[i][c]),None)
        if at is None:continue
        a[r],a[at]=a[at],a[r];d=a[r][c];a[r]=[v/d for v in a[r]]
        for i in range(len(a)):
            if i!=r and a[i][c]:
                d=a[i][c];a[i]=[x-d*y for x,y in zip(a[i],a[r])]
        pivots.append(c);r+=1
        if r==len(a):break
    basis=[]
    for free in set(range(cols))-set(pivots):
        v=[Fraction(0)]*cols;v[free]=1
        for i,c in enumerate(pivots):v[c]=-a[i][free]
        d=1
        for x in v:d=math.lcm(d,x.denominator)
        v=[int(x*d) for x in v]
        assert all(sum(x*y for x,y in zip(row,v))==0 for row in matrix)
        basis.append(v)
    return basis

def make(n,a,b,seed):
    t,word,rows=automaton(n);basis=kernel(rows);rng=random.Random(seed)
    def weights(target):
        v=[0]*n+[target*pow(n-1,-1,1<<32)&MASK]*n
        for vector in basis:
            k=rng.getrandbits(32);v=[(x+k*y)&MASK for x,y in zip(v,vector)]
        assert all(sum(x*y for x,y in zip(row,v))&MASK==target&MASK for row in rows)
        return v
    aa,bb=weights(a),weights(b)
    witness=next(({'letter':1,'states':[i,j],'a':[aa[n+i],aa[n+j]],'b':[bb[n+i],bb[n+j]]}
                  for i in range(n-1) for j in range(i+1,n-1) if (aa[n+i],bb[n+i])!=(aa[n+j],bb[n+j])),None)
    return {'n':n,'word':word,'next':t[0]+t[1],'a':aa,'b':bb,'target_a':a&MASK,'target_b':b&MASK,'seed':seed,'kernel_dimension':len(basis),'nonpotential_selfloop_witness':witness}

def summarize(info):
    out=[];n=info['n']
    for start in range(n):
        q=start;a=b=0
        for letter in info['word']:
            i=letter*n+q;a=(a+info['a'][i])&MASK;b=(b+info['b'][i])&MASK;q=info['next'][i]
        out.append([q,a,b])
    return out
