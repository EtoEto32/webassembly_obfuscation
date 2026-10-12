"""Two-pair invariant-state prototype; no Wasm or protection claim."""
from collections import defaultdict
from itertools import product
from pathlib import Path
import hashlib
import json
import platform
import random

ROOT = Path(__file__).resolve().parent


def encode(state, modulus):
    a, b, c, d = state  # two related pairs: (a,b), (c,d)
    return tuple(v % modulus for v in (a+c, b+d, a*c, b*d, a*d+c*b))


def reference(state, incoming, modulus):
    a, b, c, d = state
    # The control condition is invariant under exchange of whole pairs.
    u = incoming if ((a+c) ^ (b+d)) & 1 else incoming+1
    return ((a+b*b+u) % modulus, (b+a*a) % modulus,
            (c+d*d+u) % modulus, (d+c*c) % modulus)


def update(coeff, incoming, modulus):
    X, Y, P, Q, R = coeff
    u = incoming if (X ^ Y) & 1 else incoming+1
    bx = X+Y*Y-2*Q
    by = Y+X*X-2*P
    return tuple(v % modulus for v in (
        bx+2*u, by,
        P+Y*R-Q*X+Q*Q+u*bx+u*u,
        Q+X*R-P*Y+P*P,
        R+P*X+Q*Y+R*R-2*P*Q+u*by))


def main():
    result_path = ROOT/'results.json'
    if result_path.exists():
        raise SystemExit('Preserve previous results; use a fresh directory.')
    fibers = defaultdict(list)
    small_checks = 0
    for s in product(range(8), repeat=4):
        encoded = encode(s, 8)
        fibers[encoded].append(s)
        for u in range(8):
            assert update(encoded, u, 8) == encode(reference(s, u, 8), 8)
            small_checks += 1
    excess_fibers = []
    for encoded, states in fibers.items():
        canonical = {min(s, (s[2],s[3],s[0],s[1])) for s in states}
        if len(canonical) > 1:
            excess_fibers.append(dict(coeff=encoded, distinct_pair_orbits=len(canonical),
                                      states=states))

    # Separate scalar multisets lose which x belongs to which y.
    s1, s2 = (0,0,1,1), (0,1,1,0)
    assert encode(s1,8)[:4] == encode(s2,8)[:4]
    assert encode(reference(s1,0,8),8) != encode(reference(s2,0,8),8)

    rng = random.Random(0x43524F53)
    boundaries = [0,1,0x7fffffff,0x80000000,0xffffffff]
    cases = [(s, i & 0xffffffff) for i,s in enumerate(product(boundaries, repeat=4))]
    cases += [(tuple(rng.getrandbits(32) for _ in range(4)), rng.getrandbits(32)) for _ in range(2048)]
    large_checks = 0
    branch_counts = [0,0]
    traces = hashlib.sha256()
    for s, u in cases:
        c = encode(s, 1<<32)
        for step in range(8):
            branch_counts[(c[0]^c[1]) & 1] += 1
            s = reference(s, (u+step)&0xffffffff, 1<<32)
            c = update(c, (u+step)&0xffffffff, 1<<32)
            assert c == encode(s, 1<<32)
            traces.update(json.dumps([s,c],separators=(',',':')).encode())
            large_checks += 1
    (ROOT/'inputs32.json').write_text(json.dumps(cases)+'\n',encoding='utf-8')
    result = dict(python=platform.python_version(),seed=0x43524F53,
        small_width=3,small_input_states=4096,small_checks=small_checks,
        coefficient_states=len(fibers),extra_collision_fibers=len(excess_fibers),
        example_extra_fibers=excess_fibers[:5],
        lost_correlation=dict(states=[s1,s2],initial=[encode(s1,8),encode(s2,8)],
            next=[encode(reference(s1,0,8),8),encode(reference(s2,0,8),8)]),
        large_cases=len(cases),large_transitions=large_checks,
        branch_counts=branch_counts,mismatches=0,trace_sha256=traces.hexdigest(),
        inputs_sha256=hashlib.sha256((ROOT/'inputs32.json').read_bytes()).hexdigest(),
        status='Arithmetic prototype only; novelty and protection unproven.')
    result_path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['small_checks','coefficient_states',
        'extra_collision_fibers','large_cases','large_transitions','branch_counts','mismatches']}))


if __name__ == '__main__':
    main()
