"""Feasibility of a shared total transition under bijective representations.
Independent finite orbit check; not an obfuscation/security experiment.
"""
from itertools import permutations, product
from collections import Counter
from pathlib import Path
import json

def profile(f):
    return tuple(sorted(Counter(f).values(), reverse=True))

size = 4
functions = list(product(range(size), repeat=size))
perms = list(permutations(range(size)))
groups = {}
for f in functions:
    groups.setdefault(profile(f), []).append(f)
orbits = []
for signature, members in sorted(groups.items()):
    base = members[0]
    orbit = set()
    for p in perms:
        for q in perms:
            # q o base o p is equivalent to independently permuting input/output.
            orbit.add(tuple(q[base[p[x]]] for x in range(size)))
    assert orbit == set(members)
    orbits.append(dict(profile=signature, representative=base, count=len(members),
                       orbit_count=len(orbit)))

observations=[]
for width in range(2,9):
    modulus=1 << width
    for u in (0,1,modulus//2,modulus-1):
        add=tuple((x+u)%modulus for x in range(modulus))
        square=tuple((x*x+u)%modulus for x in range(modulus))
        pa, ps = profile(add), profile(square)
        assert pa != ps
        a,b=0,modulus//2
        assert square[a] == square[b]
        observations.append(dict(width=width,u=u,add_profile=pa,square_profile=ps,
                                 collision=[a,b],collision_output=square[a]))

result=dict(domain_size=size,total_functions=len(functions),
            permutations_each_side=len(perms),orbits=orbits,
            observations=observations,
            status='two-sided bijection feasibility gate only; no novel algorithm')
Path(__file__).with_name('results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k != 'observations'},indent=2))
print('add-vs-square cases:',len(observations))
