"""Exhaustive small GF(2) check of universal fixed-order residual mixers.

Not a hash test or a novelty claim. Enumerates ALL strictly lower linear F and
ALL mixers, not random samples. Failed mixers retain a concrete linear witness.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'artifacts' / 'mixer-class.json'


def matrix(code, n):
    return [(code >> (n*i)) & ((1 << n)-1) for i in range(n)]


def mul(a, b):
    return [xor(b[j] for j in range(len(a)) if row & (1 << j)) for row in a]


def xor(items):
    result = 0
    for item in items:
        result ^= item
    return result


def run(n):
    identity = [1 << i for i in range(n)]
    slots = [(i, j) for i in range(n) for j in range(i)]
    lowers = []
    for code in range(1 << len(slots)):
        rows = [0]*n
        for k, (i, j) in enumerate(slots):
            if code & (1 << k):
                rows[i] |= 1 << j
        lowers.append(rows)
    good, witnesses, pair_count = [], [], 0
    for code in range(1 << (n*n)):
        m = matrix(code, n)
        witness = None
        # No early exit: explicitly check every mixer/source pair.
        for lower in lowers:
            t = [a ^ b ^ c for a, b, c in zip(identity, m, mul(m, lower))]
            power = identity
            for _ in range(n):
                power = mul(power, t)
            nilpotent = not any(power)
            pair_count += 1
            if not nilpotent and witness is None:
                basis = next(j for j in range(n) if any(row & (1 << j) for row in power))
                witness = dict(mixer_code=code, lower_rows=lower, update_rows=t,
                               initial_basis=basis, nth_power_rows=power)
        predicted = all(m[i] & (1 << i) and m[i] >> (i+1) == 0 for i in range(n))
        assert predicted == (witness is None), (n, code)
        if witness is None:
            good.append(code)
        else:
            witnesses.append(witness)
    assert len(good) == 1 << (n*(n-1)//2)
    return dict(dimension=n, mixer_count=1 << (n*n), source_count=len(lowers),
                pairs=pair_count, accepted_count=len(good), accepted_codes=good,
                rejected_count=len(witnesses), witnesses=witnesses)


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    rows = [run(n) for n in (1, 2, 3)]
    report = dict(scope='All GF(2) constant mixers and all strictly lower linear maps, n=1..3',
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  results=rows)
    OUT.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps([{k: v for k, v in r.items() if k not in ('witnesses', 'accepted_codes')} for r in rows]))


if __name__ == '__main__':
    main()
