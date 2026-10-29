"""Finite gate for decoder-derived pruning. NOT an obfuscator or Neo reproduction."""
from itertools import product
from pathlib import Path
import json

WIDTH = 3
MASK = (1 << WIDTH) - 1
OPS = ('add', 'sub', 'xor', 'mul', 'and', 'or')
DOMAIN = list(product(range(MASK + 1), repeat=2))
GRAMMAR = list(product(OPS, repeat=3))

def op(name, a, b):
    return {'add': lambda: a+b, 'sub': lambda: a-b,
            'xor': lambda: a^b, 'mul': lambda: a*b,
            'and': lambda: a&b, 'or': lambda: a|b}[name]() & MASK

def observation(theta, a, b):
    u = op(theta[0], a, b)
    v = op(theta[1], u, b)
    w = op(theta[2], u, v)
    return u, v, w, b

DECODERS = [('id', i, i) for i in range(4)] + list(product(OPS, range(4), range(4)))
def decode(d, obs):
    name, i, j = d
    return obs[i] if name == 'id' else op(name, obs[i], obs[j])

TRACES = {t: [observation(t, a, b) for a, b in DOMAIN] for t in GRAMMAR}
GOOD = {}
SAMPLE_GOOD = {}
for d in DECODERS:
    GOOD[d] = {t for t in GRAMMAR if all(decode(d, obs) == a
               for (a, b), obs in zip(DOMAIN, TRACES[t]))}
    # Deliberately inadequate sample: a=0 only, all b.
    SAMPLE_GOOD[d] = {t for t in GRAMMAR if all(decode(d, obs) == a
               for (a, b), obs in zip(DOMAIN, TRACES[t]) if a == 0)}

def matches(theta, cube):
    return all(v is None or v == t for t, v in zip(theta, cube))

def generalize(theta, accepted):
    cube = list(theta)
    for axis in range(3):
        old = cube[axis]
        cube[axis] = None
        if not all(t in accepted for t in GRAMMAR if matches(t, cube)):
            cube[axis] = old
    return cube

def independent_observe(t, a, b):
    # Separate dispatch and masking, not calls to the generator's op/observation.
    def run(k, x, y):
        if k == 'add': z = x + y
        elif k == 'sub': z = x - y
        elif k == 'xor': z = x ^ y
        elif k == 'mul': z = x * y
        elif k == 'and': z = x & y
        elif k == 'or': z = x | y
        else: raise AssertionError(k)
        return z % (2 ** WIDTH)
    x = run(t[0], a, b)
    y = run(t[1], x, b)
    return (x, y, run(t[2], x, y), b), run

certificates = []
remaining = set(GRAMMAR)
verification_pairs = 0
for theta in GRAMMAR:
    if theta not in remaining:
        continue
    d = next((d for d in DECODERS if theta in GOOD[d]), None)
    if d is None:
        continue
    cube = generalize(theta, GOOD[d])
    covered = [t for t in GRAMMAR if matches(t, cube)]
    for t in covered:
        for a, b in DOMAIN:
            obs, run = independent_observe(t, a, b)
            value = obs[d[1]] if d[0] == 'id' else run(d[0], obs[d[1]], obs[d[2]])
            assert value == a, (t, d, a, b)
            verification_pairs += 1
    newly_removed = len(remaining.intersection(covered))
    remaining.difference_update(covered)
    certificates.append(dict(seed=theta, decoder=d, cube=cube,
                             covered=covered, newly_removed=newly_removed))

recoverable = set().union(*GOOD.values())
assert set(GRAMMAR) - remaining == recoverable

# Demonstrate a sample-derived cube rejecting a candidate for which this decoder fails.
counterexample = None
for theta in GRAMMAR:
    for d in DECODERS:
        if theta not in GOOD[d]:
            continue  # seed is genuinely recovered, only generalization is unsound
        cube = generalize(theta, SAMPLE_GOOD[d])
        bad = next((t for t in GRAMMAR if matches(t, cube) and t not in GOOD[d]), None)
        if bad:
            a, b = next((a, b) for a, b in DOMAIN if decode(d, observation(bad, a, b)) != a)
            counterexample = dict(seed=theta, decoder=d, cube=cube, excluded=bad,
                                  input=[a,b], expected=a,
                                  observed=decode(d, observation(bad,a,b)))
            break
    if counterexample:
        break
assert counterexample is not None

# Surviving a decoder grammar does not imply a valid representation.
collisions = []
for theta in sorted(remaining):
    seen = {}
    for a, b in DOMAIN:
        obs = observation(theta, a, b)
        if obs in seen and seen[obs] != a:
            collisions.append(dict(candidate=theta, a=seen[obs], other_a=a, b=b, observation=obs))
            break
        seen[obs] = a

result = dict(width=WIDTH, candidate_count=len(GRAMMAR), decoder_count=len(DECODERS),
              input_count=len(DOMAIN), recoverable_count=len(recoverable),
              remaining_count=len(remaining), certificate_count=len(certificates),
              independent_verification_pairs=verification_pairs,
              certificates=certificates, sample_only_counterexample=counterexample,
              survivor_collisions=collisions, remaining=sorted(remaining),
              status='finite pruning check; no novelty, Wasm, or security claim')
Path(__file__).with_name('results.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in
      ('certificates','survivor_collisions','remaining')}, indent=2))
print('survivors_with_information_loss', len(collisions))
