"""Early design counterexamples; not an obfuscator or a patentability test.

Exhaustive small rings plus 32-bit samples. Only the Python standard library.
The supplied decoders are known algebraic inverses, not synthesized attacks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random


def encode(kind, x, r, mask):
    if kind == 'identity':
        return x & mask, r & mask
    if kind == 'coupled_linear':
        return (2*x+r) & mask, (x+r) & mask
    if kind == 'quadratic_shears':
        a = (x+r*r) & mask
        return a, (r+a*a) & mask
    raise ValueError(kind)


def decode(kind, a, b, mask):
    if kind == 'identity':
        return a, b
    if kind == 'coupled_linear':
        return (a-b) & mask, (2*b-a) & mask
    if kind == 'quadratic_shears':
        r = (b-a*a) & mask
        return (a-r*r) & mask, r
    raise ValueError(kind)


def exhaustive(kind, bits):
    n = 1 << bits
    seen, buckets, witnesses = set(), [{}, {}], [None, None]
    checks, mismatches, wrong_a_mismatches = 0, 0, 0
    for x in range(n):
        for r in range(n):
            pair = encode(kind, x, r, n-1)
            seen.add(pair)
            checks += 1
            mismatches += decode(kind, *pair, n-1) != (x, r)
            wrong_a_mismatches += pair[0] != x
            for j in range(2):
                value = pair[j]
                old = buckets[j].setdefault(value, (x, r))
                if old[0] != x and witnesses[j] is None:
                    witnesses[j] = {'coordinate_value': value,
                                    'source_pairs': [list(old), [x, r]]}
    assert mismatches == 0 and len(seen) == n*n
    expected = [True, False] if kind == 'identity' else [False, False]
    single = [v is None for v in witnesses]
    assert single == expected, (kind, bits, single)
    if kind != 'identity':
        assert wrong_a_mismatches > 0
    return dict(kind=kind, bits=bits, pairs=checks, inverse_mismatches=mismatches,
                distinct_encoded_pairs=len(seen), single_coordinate_x_decoder=single,
                nonexistence_witnesses=witnesses,
                wrong_decoder_x_equals_a_mismatches=wrong_a_mismatches)


def word32(kind):
    mask = (1 << 32)-1
    edge = [0, 1, 2, (1 << 31)-1, 1 << 31, mask-1, mask]
    rng = random.Random(20261018)
    pairs = [(x, r) for x in edge for r in edge]
    pairs += [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(4096)]
    mismatches = sum(decode(kind, *encode(kind, x, r, mask), mask) != (x, r)
                     for x, r in pairs)
    assert mismatches == 0
    if kind == 'coupled_linear':
        witnesses = [[(0, 0), (1, -2)], [(0, 0), (1, -1)]]
    elif kind == 'quadratic_shears':
        witnesses = [[(0, 0), (-1, 1)], [(0, 0), (-14, -4)]]
    else:
        witnesses = [None, [(0, 0), (1, 0)]]
    records = []
    for j, w in enumerate(witnesses):
        if w is None:
            records.append(None)
            continue
        w = [(x & mask, r & mask) for x, r in w]
        enc = [encode(kind, *p, mask) for p in w]
        assert w[0][0] != w[1][0] and enc[0][j] == enc[1][j]
        records.append(dict(source_pairs=w, encoded_pairs=enc))
    return dict(kind=kind, bits=32, pairs=len(pairs), inverse_mismatches=mismatches,
                nonexistence_witnesses=records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path, help='New JSON file; never overwritten')
    args = parser.parse_args()
    kinds = ['identity', 'coupled_linear', 'quadratic_shears']
    small = [exhaustive(k, w) for k in kinds for w in [2, 3, 4, 8]]
    large = [word32(k) for k in kinds]
    report = dict(scope='Algebraic early screen; no Wasm transform, timing or novelty claim',
                  python=platform.python_version(), seed=20261018,
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  exhaustive=small, word32=large,
                  full_state_inverse_pairs=sum(x['pairs'] for x in small+large),
                  inverse_mismatches=sum(x['inverse_mismatches'] for x in small+large),
                  supplied_x_decoder_operations={'identity': 0, 'coupled_linear': 1,
                                                 'quadratic_shears': 4})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({k: report[k] for k in ['full_state_inverse_pairs',
                                           'inverse_mismatches', 'source_sha256']}))


if __name__ == '__main__':
    main()
