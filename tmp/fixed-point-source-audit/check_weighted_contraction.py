"""Check the pairwise weighted contraction, independently of a known root."""
import hashlib
import itertools
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'weighted-contraction-results.json'


def score(left, right, width, layers):
    depth = max(layers)
    mask = (1 << width)-1
    values = []
    for a, b, layer in zip(left, right, layers):
        difference = (a-b) & mask
        if difference:
            valuation = (difference & -difference).bit_length()-1
            values.append(depth*valuation+layer)
    return min(values) if values else float('inf')


def update(v, x, width):
    mask = (1 << width)-1
    f = [x, (v[0]*v[0]+1) & mask]
    residual = [(a-b) & mask for a, b in zip(v, f)]
    return [(f[0]-2*(residual[0]+residual[1])) & mask,
            (f[1]-2*residual[0]) & mask]


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    rows = []
    for width in [1, 2, 3]:
        count = 0
        domain = range(1 << width)
        for x, a, b, c, d in itertools.product(domain, repeat=5):
            u, v = [a, b], [c, d]
            before = score(u, v, width, [1, 2])
            after = score(update(u, x, width), update(v, x, width), width, [1, 2])
            assert after >= before+1
            count += 1
        rows.append(dict(width=width, pairs=count))
    rng = random.Random(2026101205)
    for _ in range(256):
        x, a, b, c, d = [rng.getrandbits(32) for _ in range(5)]
        before = score([a,b], [c,d], 32, [1,2])
        after = score(update([a,b],x,32), update([c,d],x,32),32,[1,2])
        assert after >= before+1
    report = dict(scope='Pairwise score increase for the two-node polynomial example',
                  exhaustive=rows, word32_pairs=256, seed=2026101205, mismatches=0,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    OUT.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
