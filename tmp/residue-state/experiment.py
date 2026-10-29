import pathlib,json,itertools,random,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parent

def encode(values,mask):
    # Boundary/reference-only: construct coefficient lists directly from factors.
    groups=[]
    for r in range(4):
        roots=[v for v in values if v%4==r]
        coefficients=[1]
        for v in roots:
            nxt=coefficients+[0]
            for i in range(1,len(nxt)):
                nxt[i]=(nxt[i]+v*coefficients[i-1])&mask
            coefficients=nxt
        groups.append([len(roots)]+coefficients[1:]+[0]*(3-len(roots)))
    return groups

def push(group,a,b,d,mask):
    # Division-free coefficient update for degree0..3, no individual roots.
    m,s,p,q=group
    if m==0:return [0,0,0,0]
    s2=s*s-2*p
    sp3=s*p-3*q
    ns=a*s2+b*s+m*d
    np=0;nq=0
    if m>=2:
        np=a*a*(p*p-2*s*q)+a*b*sp3+(m-1)*a*d*s2+b*b*p+(m-1)*b*d*s+(m*(m-1)//2)*d*d
    if m==3:
        nq=a**3*q*q+a*a*b*p*q+a*a*d*(p*p-2*s*q)+a*b*b*s*q+a*b*d*sp3+a*d*d*s2+b**3*q+b*b*d*p+b*d*d*s+d**3
    return [m,ns&mask,np&mask,nq&mask]

def merge(left,right,mask):
    m,s,p,q=left;n,t,v,w=right
    if m+n>3:raise ValueError('coefficient capacity exceeded')
    return [m+n,(s+t)&mask,(p+s*t+v)&mask,(q+p*t+s*v+w)&mask]

def transformed(groups,u,mode,mask):
    total=sum(g[1] for g in groups)&mask
    result=[[0,0,0,0] for _ in range(4)];routes=[]
    for r,g in enumerate(groups):
        if mode=='permute':a,b,d=2,1+2*(total&1),u+2*(r&1)
        else:a,b,d=1,1+2*(r&1),u+2*(r&1)
        dest=(a*r*r+b*r+d)&3
        nxt=push(g,a,b,d,mask)
        routes.append({'source':r,'destination':dest,'count':g[0]})
        result[dest]=merge(result[dest],nxt,mask)
    return result,routes

def reference(values,u,mode,mask):
    total=sum(values)%(mask+1);out=[]
    for x in values:
        if mode=='permute':
            value=x+2*x*x+2*(total%2)*x+u
            if x%2:value+=2
        else:
            value=x*x+x+u
            if x%2:value+=2*x+2
        out.append(value%(mask+1))
    return out

def main():
    # Exact one-step checks include all four-bit inputs; i32 adds multistep coverage.
    suites={4:list(itertools.product(range(16),repeat=4))}
    boundary=[0,1,2,3,4,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    cases=[(*xs,u) for xs in itertools.product(boundary,repeat=3) for u in [0,1,2,3,0xffffffff]]
    rng=random.Random(1729)
    cases += [tuple(rng.getrandbits(32) for _ in range(4)) for _ in range(1024)]
    suites[32]=cases
    summary=[];samples=[]
    for width,inputs in suites.items():
        mask=(1<<width)-1
        for mode in ['permute','merge']:
            failures=[];count_hist=collections.Counter();merges=0;transitions=0;singletons=0;digest=hashlib.sha256()
            for idx,args in enumerate(inputs):
                roots=list(args[:3]);u=args[3];groups=encode(roots,mask)
                rounds=1 if width==4 else [0,1,2,3,15,31][idx%6]
                for step in range(rounds):
                    observed,routes=transformed(groups,u,mode,mask)
                    roots=reference(roots,u,mode,mask)
                    expected=encode(roots,mask)
                    if observed!=expected:failures.append({'input':args,'step':step,'expected':expected,'actual':observed})
                    destinations=[r['destination'] for r in routes if r['count']]
                    merges+=len(destinations)-len(set(destinations))
                    count_hist.update(g[0] for g in observed)
                    singletons+=sum(g[0]==1 for g in observed)
                    transitions+=1
                    digest.update(json.dumps([width,mode,idx,step,observed],separators=(',',':')).encode())
                    if idx<4 or (width==32 and idx in [3644,3645]):samples.append({'width':width,'mode':mode,'input':args,'step':step,'groups':observed,'reference_values':roots[:],'routes':routes})
                    groups=observed
            summary.append({'width':width,'mode':mode,'input_cases':len(inputs),'transitions':transitions,'failures':failures[:16],'failure_count':len(failures),'class_size_histogram':dict(count_hist),'source_class_merges':merges,'singleton_groups_exposing_individual_values':singletons,'trace_sha256':digest.hexdigest()})
    (ROOT/'inputs32.json').write_text(json.dumps(cases))
    (ROOT/'samples.json').write_text(json.dumps(samples,indent=2))
    (ROOT/'results.json').write_text(json.dumps({'seed':1729,'summary':summary},indent=2))
    print(json.dumps(summary))
    assert not any(row['failure_count'] for row in summary)
if __name__=='__main__':main()
