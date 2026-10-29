"""Elementary prime-field polynomial operations; not a novel factoring method."""
import random
P = 4294967291

def trim(a):
    a = list(a)
    while len(a)>1 and a[-1]==0: a.pop()
    return a or [0]

def add(a,b):
    return trim([((a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0))%P
                 for i in range(max(len(a),len(b)))])

def mul(a,b):
    c=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b): c[i+j]=(c[i+j]+x*y)%P
    return trim(c)

def divrem(a,b):
    a=trim(a);b=trim(b)
    if b==[0]: raise ZeroDivisionError()
    q=[0]*max(1,len(a)-len(b)+1); inv=pow(b[-1],-1,P)
    while a!=[0] and len(a)>=len(b):
        d=len(a)-len(b);c=a[-1]*inv%P;q[d]=c
        for j,y in enumerate(b): a[d+j]=(a[d+j]-c*y)%P
        a=trim(a)
    return trim(q),a

def gcd(a,b):
    while b!=[0]: a,b=b,divrem(a,b)[1]
    inv=pow(a[-1],-1,P)
    return [x*inv%P for x in a]

def evaluate(a,x):
    v=0
    for c in reversed(a): v=(v*x+c)%P
    return v

def power(a,n,m):
    r=[1]
    while n:
        if n&1:r=divrem(mul(r,a),m)[1]
        n>>=1
        if n:a=divrem(mul(a,a),m)[1]
    return r

def encode(items):
    items=sorted(items);p=[1]
    for k,v in items:p=mul(p,[-k%P,1])
    lo=[0];hi=[0]
    for k,v in items:
        q,rem=divrem(p,[-k%P,1]);assert rem==[0]
        d=pow(evaluate(q,k),-1,P)
        lo=add(lo,[c*d*(v%P)%P for c in q])
        hi=add(hi,[c*d*(v//P)%P for c in q])
    n=len(items)
    return p,lo+[0]*(n-len(lo)),hi+[0]*(n-len(hi))

def roots(f,seed=271021,limit=256):
    """Known equal-degree splitting, d=1. Return a verifiable factor certificate."""
    f=trim(f)
    if f==[1]:return [],dict(split_attempts=0,multiplied_back=True)
    if f[-1]!=1: raise ValueError('monic polynomial required')
    rng=random.Random(seed);todo=[f];out=[];attempts=0
    while todo:
        g=todo.pop()
        if len(g)==2:out.append(-g[0]%P);continue
        for attempt in range(limit):
            a=[rng.randrange(P),1];h=gcd(g,a);attempts+=1
            if 1<len(h)<len(g):break
            h=gcd(g,add(power(a,(P-1)//2,g),[P-1]))
            if 1<len(h)<len(g):break
        else:raise TimeoutError('split attempt limit; not resistance evidence')
        other,rem=divrem(g,h);assert rem==[0];todo.extend([h,other])
    out.sort();rebuilt=[1]
    for x in out:rebuilt=mul(rebuilt,[-x%P,1])
    if rebuilt!=f or len(set(out))!=len(out):raise ValueError('factor verification failed')
    return out,dict(split_attempts=attempts,multiplied_back=True)
