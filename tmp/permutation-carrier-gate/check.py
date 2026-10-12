"""Finite mathematical gate for a permutation-parity carrier. Not an obfuscator."""
from itertools import permutations,product
from pathlib import Path
import json

def compose(a,b): return tuple(a[b[i]] for i in range(len(a)))
def inverse(a): return tuple(a.index(i) for i in range(len(a)))
def parity(a): return sum(a[i]>a[j] for i in range(len(a)) for j in range(i+1,len(a)))%2
def commutator(a,b): return compose(compose(compose(a,b),inverse(a)),inverse(b))
def full_cycle(a):
    seen=set();i=0
    while i not in seen: seen.add(i);i=a[i]
    return len(seen)==len(a) and i==0

perms=list(permutations(range(5)));identity=tuple(range(5));pairs=0
for a,b in product(perms,repeat=2):
    assert parity(compose(a,b))==parity(a)^parity(b)
    assert parity(commutator(a,b))==0
    pairs+=1
# Closure in the observer's Boolean domain: signs of constants, input carriers,
# products, inverses and conjugations. Inversion leaves parity unchanged.
domain={(0,0,0,0),(1,1,1,1),(0,0,1,1),(0,1,0,1)}
while True:
    expanded=domain|{tuple(x^y for x,y in zip(a,b)) for a,b in product(domain,repeat=2)}
    if expanded==domain:break
    domain=expanded
and_table=(0,0,0,1);assert and_table not in domain and len(domain)==8
# Different carrier: false=identity, true=a specific five-cycle. A known
# noncommutative construction supports AND; parity does not distinguish it.
a=(1,2,3,4,0)
b=next(p for p in perms if full_cycle(p) and full_cycle(commutator(a,p)))
c=commutator(a,b);truth=[]
for x,y in product((0,1),repeat=2):
    r=commutator(a if x else identity,b if y else identity)
    assert r==(c if x and y else identity)
    truth.append({'x':x,'y':y,'output':r,'output_parity':parity(r),'is_true_cycle':r==c})
report={'scope':'Exact S5 enumeration plus abstract parity closure; not a general impossibility for graphs or a security test.',
        'permutations':len(perms),'ordered_pairs':pairs,'parity_mismatches':0,
        'reachable_two_input_parity_truth_tables':sorted(domain),'and_reachable':False,
        'different_known_carrier_example':{'a':a,'b':b,'commutator':c,'truth':truth}}
Path(__file__).with_name('results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
