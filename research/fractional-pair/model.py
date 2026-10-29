"""Independent integer arithmetic check of the stated perturbation interval."""
import argparse,json,math,random
from pathlib import Path
def pair(w,x,d,t):
    a=1<<w;z=(a*x+t)//d
    return z//a,((z%a)*d+d-1)//a
def run(output):
    rows=[];counterexamples=[]
    for w in range(2,7):
        a=1<<w;count=0
        for d in range(1,a):
            valid=[]
            for t in range(a):
                ok=True
                for x in range(a):
                    count+=1
                    if pair(w,x,d,t)!=divmod(x,d):ok=False
                valid.append(ok)
            bound=a-d+math.gcd(a,d)-1
            assert valid==[t<=bound for t in range(a)],(w,d,bound,valid)
            if bound+1<a:
                x=next(x for x in range(a) if pair(w,x,d,bound+1)!=divmod(x,d))
                counterexamples.append(dict(w=w,x=x,d=d,t=bound+1,got=pair(w,x,d,bound+1),expected=divmod(x,d)))
        rows.append(dict(w=w,comparisons=count))
    rng=random.Random(221028);count=0;wide_bad=[];a=1<<32
    for k in range(10000):
        x=rng.randrange(a);d=rng.randrange(1,a);g=math.gcd(a,d);bound=a-d+g-1
        for t in (0,bound,rng.randrange(bound+1)):
            assert pair(32,x,d,t)==divmod(x,d);count+=1
        if bound+1<a:
            t=bound+1;r=(-(t//g)*pow(a//g,-1,d//g))%(d//g)
            assert pair(32,r,d,t)!=divmod(r,d)
            if len(wide_bad)<16:wide_bad.append(dict(x=r,d=d,t=t,got=pair(32,r,d,t),expected=divmod(r,d)))
    result=dict(small=rows,comparisons=sum(r['comparisons'] for r in rows),small_counterexamples=counterexamples,wide_comparisons=count,wide_counterexamples=wide_bad,seed=221028)
    with Path(output).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('small_counterexamples','wide_counterexamples')}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');run(ap.parse_args().output)
