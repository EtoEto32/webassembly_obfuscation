import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import re
import time

import numpy as np

HERE = Path(__file__).resolve().parent
VENDOR = HERE.parent / 'sha256-research-baseline/vendor/sha256.js'


def inverse(p):
    assert np.array_equal(np.sort(p), np.arange(len(p)))
    result = np.empty_like(p)
    result[p] = np.arange(len(p))
    assert np.array_equal(p[result], np.arange(len(p)))
    return result


def cycles(p):
    inverse(p)  # Check permutation before interpreting the traversal.
    seen = bytearray(len(p))
    counts = Counter()
    for x in range(len(p)):
        if seen[x]:
            continue
        length = 0
        y = x
        while not seen[y]:
            seen[y] = 1
            length += 1
            y = int(p[y])
        assert y == x
        counts[length] += 1
    assert sum(k*v for k, v in counts.items()) == len(p)
    return dict(sorted(counts.items()))


def round_maps(w):
    mask = (1 << w) - 1
    idx = np.arange(1 << (8*w), dtype=np.int64)
    a, b, c, d, e, f, g, h = [(idx >> (w*j)) & mask for j in range(8)]

    def r(x, n):
        n %= w
        return ((x >> n) | (x << (w-n))) & mask

    t2 = ((r(a, 2) ^ r(a, 13) ^ r(a, 22)) + ((a & b) | (c & (a | b)))) & mask
    base = h + (r(e, 6) ^ r(e, 11) ^ r(e, 25)) + (g ^ (e & (f ^ g)))
    maps = []
    for u in range(1 << w):
        t1 = (base + u) & mask
        out = [(t1+t2) & mask, a, b, c, (d+t1) & mask, e, f, g]
        p = sum(x << (w*j) for j, x in enumerate(out))
        inv = inverse(p)
        # Independent inverse-round formula for every output state.
        A, B, C, D, E, F, G, H = [(idx >> (w*j)) & mask for j in range(8)]
        q = (r(B, 2) ^ r(B, 13) ^ r(B, 22)) + ((B & C) ^ (B & D) ^ (C & D))
        T = (A-q) & mask
        old_h = (T-(r(F, 6) ^ r(F, 11) ^ r(F, 25))-((F & G) ^ ((~F) & H))-u) & mask
        old = [B, C, D, (E-T) & mask, F, G, H, old_h]
        expected = sum(x << (w*j) for j, x in enumerate(old))
        assert np.array_equal(inv, expected)
        maps.append(p)
    return maps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=HERE/'artifacts')
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    protocol = json.loads((HERE/'protocol.json').read_text())
    K = [int(x, 16) for x in re.findall(r'0x[0-9A-Fa-f]+', VENDOR.read_text().split('var K = [')[1].split(']')[0])]
    rows = []
    for w in protocol['widths']:
        maps = round_maps(w)
        size = len(maps[0])
        ident = np.arange(size)
        for length in protocol['window_lengths']:
            words = []
            for phase in protocol['phases']:
                prefixes = []
                for impulse in (None, 0, length-1):
                    p = ident.copy()
                    for t in range(length):
                        p = maps[(K[phase+t] + (t == impulse)) % (1 << w)][p]
                    prefixes.append(p)
                p0inv = inverse(prefixes[0])
                A, B = [p0inv[p] for p in prefixes[1:]]
                words.append([A[B], A[B[inverse(A)[inverse(B)]]]])
            hist = [[cycles(p) for p in pair] for pair in words]
            different = [hist[0][j] != hist[1][j] for j in range(2)]
            # Every relabeling must preserve each tested cycle histogram.
            relabel = (ident*5+7) % size
            ri = inverse(relabel)
            for j in range(2):
                assert cycles(relabel[words[0][j][ri]]) == hist[0][j]
            record = {'width': w, 'length': length, 'states': size,
                      'histograms_by_phase': hist, 'different': different}
            rows.append(record)
            # Save complete permutations, including nondistinguishing cases.
            np.savez(out/f'w{w}-L{length}.npz', phase8_product=words[0][0],
                     phase8_commutator=words[0][1], phase9_product=words[1][0],
                     phase9_commutator=words[1][1])
            assert time.monotonic()-start < 120, 'registered runtime limit'
    # Histogram equality is necessary, not sufficient for simultaneous conjugacy.
    toy_a = np.array([1, 0, 3, 2])
    toy_b = np.array([2, 3, 0, 1])
    assert cycles(toy_a) == cycles(toy_b)
    assert cycles(toy_a[toy_a]) != cycles(toy_a[toy_b])
    results = {'python': platform.python_version(), 'numpy': np.__version__,
               'scope': protocol['scope'], 'rows': rows,
               'distinguishing_cases': sum(any(r['different']) for r in rows),
               'inverse_round_checks': sum((1 << w)*(1 << (8*w)) for w in protocol['widths']),
               'relabel_checks': len(rows)*2,
               'pair_control': {'individual_histograms_equal': True, 'product_histograms_differ': True},
               'source_hashes': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [Path(__file__).resolve(), HERE/'protocol.json', VENDOR]}}
    (out/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k: v for k, v in results.items() if k not in ('rows', 'source_hashes')}))
    for r in rows:
        if any(r['different']):
            print(json.dumps(r))


if __name__ == '__main__':
    main()
