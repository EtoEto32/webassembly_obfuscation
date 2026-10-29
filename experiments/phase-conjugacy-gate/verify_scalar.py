"""Independent scalar forward evaluation of the distinguishing reduced model."""
import hashlib
import json
from pathlib import Path
import re
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE/'artifacts/scalar-verification.json'
assert not OUT.exists()
vendor = HERE.parent/'sha256-research-baseline/vendor/sha256.js'
K = [int(x, 16) & 3 for x in re.findall(r'0x[0-9A-Fa-f]+', vendor.read_text().split('var K = [')[1].split(']')[0])]


def rotate(x, n):
    s = f'{x:02b}'
    n %= 2
    return int(s[-n:]+s[:-n], 2) if n else x


sigma0 = [rotate(x, 2)^rotate(x, 13)^rotate(x, 22) for x in range(4)]
sigma1 = [rotate(x, 6)^rotate(x, 11)^rotate(x, 25) for x in range(4)]


def prefix(index, phase, impulse):
    state = [(index // (4**j)) % 4 for j in range(8)]
    for t in range(7):
        a, b, c, d, e, f, g, h = state
        ch = (e & f) ^ ((3 ^ e) & g)
        maj = (a & b) ^ (a & c) ^ (b & c)
        t1 = (h + sigma1[e] + ch + K[phase+t] + (t == impulse)) % 4
        t2 = (sigma0[a] + maj) % 4
        state = [(t1+t2) % 4, a, b, c, (d+t1) % 4, e, f, g]
    return sum(x*(4**j) for j, x in enumerate(state))


def inv(p):
    q = [-1]*len(p)
    for i, x in enumerate(p):
        assert q[x] == -1
        q[x] = i
    assert -1 not in q
    return q


saved = np.load(HERE/'artifacts/w2-L7.npz')
counts = []
for phase in (8, 9):
    p0, pa, pb = [[prefix(x, phase, impulse) for x in range(65536)] for impulse in (None, 0, 6)]
    p0i = inv(p0)
    A = [p0i[x] for x in pa]
    B = [p0i[x] for x in pb]
    Ai, Bi = inv(A), inv(B)
    product = [A[B[x]] for x in range(65536)]
    commutator = [A[B[Ai[Bi[x]]]] for x in range(65536)]
    assert product == saved[f'phase{phase}_product'].tolist()
    assert commutator == saved[f'phase{phase}_commutator'].tolist()
    counts.append(sum(x == y for x, y in enumerate(commutator)))
assert counts == [80, 48]
result = {'fixed_points': counts, 'phases': [8, 9], 'width': 2,
          'full_permutation_entries_verified': 4*65536,
          'scalar_round_evaluations': 2*3*65536*7,
          'hashes': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in [Path(__file__).resolve(), vendor, HERE/'artifacts/w2-L7.npz']}}
OUT.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({k: v for k, v in result.items() if k != 'hashes'}))
