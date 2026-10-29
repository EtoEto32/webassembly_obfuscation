"""Exhaustive small-word audit of the fixed native-opcode compatibility claim."""
import json,sys
from pathlib import Path
def study(w):
    n=1<<w;mask=n-1;rows=[];accepted=[];checks=0
    for a in range(1,n,2):
        for b in range(n):
            e=[(a*x+b)&mask for x in range(n)];inverse=[e.index(x) for x in range(n)]
            failures=[];ok=[]
            for target in ('and','or'):
                # Set encoded old to all-ones (AND) or zero (OR) to force operand T(y).
                z=inverse[mask if target=='and' else 0];t=[e[z&y] for y in range(n)];witness=None
                for x in range(n):
                    for y in range(n):
                        checks+=1;actual=e[x]&t[y] if target=='and' else e[x]|t[y]
                        if actual!=e[x&y]:witness=dict(x=x,y=y,expected=e[x&y],actual=actual);break
                    if witness:break
                if witness:failures.append(dict(target=target,**witness))
                else:ok.append(target)
            if ok:accepted.append(dict(a=a,b=b,targets=ok))
            else:rows.append(dict(a=a,b=b,failures=failures))
    assert [(r['a'],r['b']) for r in accepted]==[(1,0),(mask,mask)]
    return dict(width=w,affine_candidates=n*n//2,checks=checks,accepted=accepted,rejected=rows)
if __name__=='__main__':
    p=Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise FileExistsError(p)
    r=[study(w) for w in range(2,7)];p.write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in x.items() if k!='rejected'} for x in r]))
