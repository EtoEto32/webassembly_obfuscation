import collections
import hashlib
import itertools
import json
import platform
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent


def compose(f,g): return tuple(f[g[x]] for x in range(len(g)))


def inverse(p):
    q=[0]*len(p)
    for x,y in enumerate(p): q[y]=x
    return tuple(q)


def cycles(p):
    seen=set(); result=[]
    for start in range(len(p)):
        if start in seen: continue
        c=[]; x=start
        while x not in seen:
            seen.add(x);c.append(x);x=p[x]
        assert x==start
        result.append(c)
    return result


def root(p):
    groups=collections.defaultdict(list)
    for c in cycles(p): groups[len(c)].append(c)
    if any(n%2==0 and len(cs)%2 for n,cs in groups.items()): return None
    u=[None]*len(p)
    for n,cs in groups.items():
        if n%2:
            # Twice this stride equals one modulo odd cycle length.
            for c in cs:
                for j,x in enumerate(c): u[x]=c[(j+(n+1)//2)%n]
        else:
            for a,b in zip(cs[::2],cs[1::2]):
                for j in range(n):
                    u[a[j]]=b[j]
                    u[b[j]]=a[(j+1)%n]
    return tuple(u)


def main():
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    perms=list(itertools.permutations(range(4)))
    # Oracle uses direct composition of all permutations, not cycle conditions.
    squares=collections.defaultdict(list)
    for u in perms: squares[compose(u,u)].append(u)
    for p in perms:
        candidate=root(p)
        assert (candidate is not None)==(p in squares)
        if candidate is not None: assert compose(candidate,candidate)==p
    assert root(tuple(range(4))) is not None
    assert root((1,0,2,3)) is None
    records=[]; checks=0; sample=None
    for a in perms:
        for b in perms:
            p=compose(b,a);u=root(p)
            record={'T0':a,'T1':b,'composition':p,'cycles':cycles(p),'feasible':u is not None}
            if u is not None:
                e1=compose(u,inverse(a))
                d1=inverse(e1)
                for x in range(4):
                    assert u[x]==e1[a[x]]
                    assert u[e1[x]]==b[x]
                    assert d1[u[x]]==a[x]
                    checks+=2
                record.update({'U':u,'E1':e1,'D1':d1})
                if sample is None and compose(a,b)!=compose(b,a): sample=record
            records.append(record)
    assert sample is not None
    target=[];repair_checks=0
    for w in range(1,9):
        n=1<<w
        a=tuple((x+1)%n for x in range(n))
        b=tuple(x^1 for x in range(n))
        p=compose(b,a)
        u=root(p)
        assert (u is not None)==(w==1)
        # Labeled pair (x,h) is packed as 2*x+h. This is a model, not a claim of hidden h.
        lifted=tuple(2*x+1 if h==0 else 2*p[x] for x in range(n) for h in (0,1))
        e0=tuple(2*x for x in range(n))
        ai=inverse(a)
        e1=tuple(2*ai[y]+1 for y in range(n))
        for x in range(n):
            assert lifted[e0[x]]==e1[a[x]]
            assert lifted[e1[x]]==e0[b[x]]
            assert lifted[lifted[e0[x]]]==e0[p[x]]
            repair_checks+=2
        target.append({'width':w,'N':n,'cycles':cycles(p),'root_exists':u is not None,
                       'repair_U':lifted,'repair_E0':e0,'repair_E1':e1})
    report={'python':platform.python_version(),'permutations':len(perms),'distinct_squares':len(squares),
            'operation_pairs':len(records),'feasible_pairs':sum(r['feasible'] for r in records),
            'constructed_transition_checks':checks,'repair_transition_checks':repair_checks,
            'target':target,'noncommuting_positive_control':sample,
            'source_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'check.py',HERE/'protocol.json']}}
    (out/'pairs.json').write_text(json.dumps(records,indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'sample.json').write_text(json.dumps(sample,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['permutations','distinct_squares','operation_pairs','feasible_pairs',
                                         'constructed_transition_checks','repair_transition_checks']},indent=2))


if __name__=='__main__': main()
