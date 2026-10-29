"""Check a polynomial bit-circuit lift of the real SHA-256 T2 expression.

This is a local evaluator experiment, not a complete hash or a novelty claim.
Each original bit is represented by one ring element in Z/(2**w).
"""
import hashlib
import json
import platform
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'bitlift-results.json'
EXTERNAL = 98  # a,b,c bits (96), zero, one
gates = []
depths = [0] * EXTERNAL


def gate(op, a, b):
    ref = EXTERNAL + len(gates)
    gates.append((op, a, b))
    depths.append(1 + max(depths[a], depths[b]))
    return ref


def polynomial(op, a, b):
    if op == 'xor':
        return a + b - 2*a*b
    if op == 'and':
        return a*b
    if op == 'or':
        return a + b - a*b
    raise ValueError(op)


sigma = [gate('xor', gate('xor', (i+2) % 32, (i+13) % 32),
              (i+22) % 32) for i in range(32)]
majority = []
for i in range(32):
    ab = gate('and', i, 32+i)
    ac = gate('and', i, 64+i)
    bc = gate('and', 32+i, 64+i)
    majority.append(gate('xor', gate('xor', ab, ac), bc))
carry, output = 96, []
for i in range(32):
    p = gate('xor', sigma[i], majority[i])
    output.append(gate('xor', p, carry))
    if i != 31:  # overflow is discarded in 32-bit addition
        carry = gate('or', gate('and', sigma[i], majority[i]),
                     gate('and', p, carry))
DEPTH = max(depths)
N = len(gates)


def inputs(words):
    return [(x >> i) & 1 for x in words for i in range(32)] + [0, 1]


def reference(external):
    values = external[:]
    for op, a, b in gates:
        value = polynomial(op, values[a], values[b])
        assert value in (0, 1)
        values.append(value)
    return values[EXTERNAL:]


def extract(root):
    return sum(root[ref-EXTERNAL] << i for i, ref in enumerate(output))


def rotr(x, n):
    return ((x >> n) | (x << (32-n))) & 0xffffffff


def t2(a, b, c):
    return ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) +
            ((a & b) ^ (a & c) ^ (b & c))) & 0xffffffff


def settle(external, root, width, initial):
    mask = (1 << width)-1
    v = initial[:]
    for step in range(1, DEPTH*width+1):
        old = external + v
        f = [polynomial(op, old[a], old[b]) & mask for op, a, b in gates]
        residual = [(a-b) & mask for a, b in zip(v, f)]
        # A has a diagonal plus a cyclic forward edge; update is synchronous.
        v = [(f[i] - 2*(residual[i]+residual[(i+1) % N])) & mask
             for i in range(N)]
        if step % DEPTH == 0:
            low = (1 << (step//DEPTH))-1
            assert all(((a-b) & low) == 0 for a, b in zip(v, root))
    assert v == root
    return extract(v)


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    rng = random.Random(2026101203)
    words = [(0, 0, 0), (0xffffffff,)*3, (1, 0, 0),
             (0x80000000, 1, 0xffffffff), (0xaaaaaaaa, 0x55555555, 0x12345678)]
    words += [tuple(rng.getrandbits(32) for _ in range(3)) for _ in range(12)]
    rows = []
    for width in [1, 2, 8, 32]:
        for xyz in words:
            ext = inputs(xyz)
            root = reference(ext)
            expected = t2(*xyz)
            assert extract(root) == expected
            for kind in ['all-max', 'seeded']:
                initial = ([(1 << width)-1]*N if kind == 'all-max' else
                           [rng.getrandbits(width) for _ in range(N)])
                actual = settle(ext, root, width, initial)
                assert actual == expected
                rows.append(dict(ring_width=width, input=list(xyz), initial=kind,
                                 iterations=DEPTH*width, expected=expected, actual=actual))
    report = dict(scope='SHA-256 T2 local expression only, Python polynomial evaluator',
                  python=platform.python_version(), seed=2026101203,
                  gates=N, depth=DEPTH, word_bits=32,
                  cases=len(rows), mismatches=0,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  results=rows)
    OUT.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}))


if __name__ == '__main__':
    main()
