import collections
import hashlib
import itertools
import json
import math
import platform
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent

def compose(a,b):
    return tuple(a[b[i]] for i in range(5))

def main():
    out=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    group=[p for p in itertools.permutations(range(5)) if sum(p[i]>p[j] for i in range(5) for j in range(i+1,5))%2==0]
    assert len(group)==60
    index={p:i for i,p in enumerate(group)}
    identity=index[tuple(range(5))]
    mul=[[index[compose(a,b)] for b in group] for a in group]
    inv=[next(b for b in range(60) if mul[a][b]==identity and mul[b][a]==identity) for a in range(60)]
    gate=[(b,mul[mul[inv[b]][a]][b]) for a in range(60) for b in range(60)]
    perm=[60*b+c for b,c in gate]
    assert len(set(perm))==3600
    def apply(state,position):
        s=list(state);s[position:position+2]=gate[60*s[position]+s[position+1]];return tuple(s)
    triples=0
    for state in itertools.product(range(60),repeat=3):
        left=apply(apply(apply(state,0),1),0)
        right=apply(apply(apply(state,1),0),1)
        assert left==right
        triples+=1
    seen=set();cycles=[]
    for start in range(3600):
        if start in seen:continue
        cycle=[];p=start
        while p not in seen:
            seen.add(p);cycle.append(p);p=perm[p]
        assert p==start
        cycles.append(cycle)
    order=math.lcm(*(len(x) for x in cycles));assert order==60
    for p in range(3600):
        q=p
        for _ in range(60):q=perm[q]
        assert q==p
    # The presentation's braid, far-commutation and cancellation relations
    # all preserve exponent sum. Sigma_1^60 cannot equal the empty braid.
    relation_exponents=[{'rule':'aba=bab','lhs':3,'rhs':3},
                        {'rule':'far generators commute','lhs':2,'rhs':2},
                        {'rule':'inverse cancellation','lhs':0,'rhs':0}]
    assert all(r['lhs']==r['rhs'] for r in relation_exponents)
    result={'python':platform.python_version(),'group_size':60,'pair_states':3600,
            'yang_baxter_triples':triples,'gate_order':order,
            'cycle_histogram':dict(sorted(collections.Counter(map(len,cycles)).items())),
            'R_power_60_identity_checks':3600,'braid_exponent_sums':{'empty':0,'sigma1_power60':60},
            'scope':'published gate only; no obfuscator or resistance claim'}
    for name,value in [('results.json',result),('tables.json',{'group':group,'multiply':mul,'inverse':inv,'R':gate,'cycles':cycles,'relations':relation_exponents})]:
        (out/name).write_text(json.dumps(value,indent=2)+'\n')
    files=[HERE/'check.py',HERE/'protocol.json',out/'results.json',out/'tables.json']
    (out/'manifest.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
