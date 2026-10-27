"""Exhaustive finite checks of the unchanged-copy commutation constraint."""
import argparse,itertools,json,math,time
from pathlib import Path

def investigate(q,n,all_maps=False):
    begin=time.perf_counter();states=list(itertools.product(range(q),repeat=n));index={x:i for i,x in enumerate(states)};S=len(states)
    transitions=[]
    for d in range(n):
        for s in range(n):
            if d==s:continue
            target=[]
            for x in states:
                y=list(x);y[d]=x[s];target.append(index[tuple(y)])
            transitions.append(target)
    survivors=[];tested=0
    choices=itertools.product(range(S),repeat=S) if all_maps else itertools.permutations(range(S))
    for e in choices:
        tested+=1
        if all(e[t[x]]==t[e[x]] for t in transitions for x in range(S)):survivors.append(e)
    unary=itertools.product(range(q),repeat=q) if all_maps else itertools.permutations(range(q))
    expected={tuple(index[tuple(pi[a] for a in x)] for x in states) for pi in unary}
    assert set(survivors)==expected
    return dict(alphabet=q,cells=n,bijective=not all_maps,maps_tested=tested,commuting=len(survivors),expected=len(expected),class_equal=True,elapsed_s=time.perf_counter()-begin,survivors=[list(e) for e in survivors])

def locality_counterexample():
    def E(x):
        x=list(x)
        for i in range(0,len(x),2):
            if (x[i]^x[i+1])&1:x[i],x[i+1]=x[i+1],x[i]
        return x
    def copy(x,d,s,n):
        y=x[:];y[d:d+n]=x[s:s+n];return y
    x=[0,1,2,3];left=E(copy(x,0,1,1));right=copy(E(x),0,1,1)
    assert left!=right and E(E(x))==x
    count=0
    for a in itertools.product(range(4),repeat=4):
        x=list(a)
        for d in (0,2,4):
            for s in (0,2,4):
                for n in (0,2,4):
                    if max(d,s)+n<=4:
                        count+=1;assert E(copy(x,d,s,n))==copy(E(x),d,s,n)
    return dict(byte_copy_counterexample=dict(input=[0,1,2,3],d=0,s=1,n=1,encode_after_copy=left,copy_after_encode=right),aligned_pair_checks=count)

def directed_check():
    # One-way copy only: cell 1 <- cell 0, alphabet size 3.
    q=3;states=list(itertools.product(range(q),repeat=2));idx={x:i for i,x in enumerate(states)}
    c=[idx[(a,a)] for a,b in states];survivors=set()
    for e in itertools.permutations(range(9)):
        if all(e[c[i]]==c[e[i]] for i in range(9)):survivors.add(e)
    expected=set()
    for pi in itertools.permutations(range(q)):
        choices=[[rho for rho in itertools.permutations(range(q)) if rho[a]==pi[a]] for a in range(q)]
        for rows in itertools.product(*choices):expected.add(tuple(idx[(pi[a],rows[a][b])] for a,b in states))
    assert survivors==expected and len(survivors)==48
    e=tuple(idx[(a,(2*b-a)%3)] for a,b in states);assert e in survivors
    reverse=[idx[(b,b)] for a,b in states]
    witness=next(i for i in range(9) if e[reverse[i]]!=reverse[e[i]])
    return dict(maps_tested=math.factorial(9),commuting=len(survivors),predicted=len(expected),class_equal=True,mixed_example=[list(states[j]) for j in e],reverse_copy_counterexample=dict(input=list(states[witness]),encode_after_copy=list(states[e[reverse[witness]]]),copy_after_encode=list(states[reverse[e[witness]]])))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');v=a.parse_args();f=Path(v.output)
    if f.exists():raise FileExistsError(f)
    rows=[investigate(2,2),investigate(2,3),investigate(3,2),investigate(2,2,True)]
    f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(dict(rows=rows,counterexample=locality_counterexample(),directed=directed_check()),indent=2));print(json.dumps([dict(maps=x['maps_tested'],survivors=x['commuting']) for x in rows]))
