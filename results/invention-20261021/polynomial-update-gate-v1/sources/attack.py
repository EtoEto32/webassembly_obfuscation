"""Only the two coefficient byte snapshots are inputs; no source/oracle/factoring."""
import argparse
import json
import struct
import time
from pathlib import Path

P = 4294967291


def parse(data):
    if len(data) < 32 or len(data) % 4:
        raise ValueError('snapshot length')
    words = list(struct.unpack('<'+'I'*(len(data)//4), data))
    n, flags = words[:2]
    if n > 512 or flags > 31 or len(words) != 8+3*n:
        raise ValueError('snapshot header')
    poly = words[7:8+n]
    lo, hi = words[8+n:8+2*n], words[8+2*n:]
    if poly[-1] != 1 or any(x >= P for x in poly+lo+hi):
        raise ValueError('field coefficients / monic P')
    return n, flags, words[2:7], poly, lo, hi


def evaluate(a, k):
    r = 0
    for x in reversed(a):
        r = (r*k+x) % P
    return r


def recover(before, after):
    n, flags, ex, poly, lo, hi = parse(before)
    m, flags2, ex2, poly2, lo2, hi2 = parse(after)
    if (n, flags, poly) != (m, flags2, poly2):
        return dict(status='unsupported_key_set_change')
    d = [[(y-x) % P for x, y in zip(a, b)] for a, b in ((lo, lo2), (hi, hi2))]
    changed = [i for i in range(5) if ex[i] != ex2[i]]
    if changed:
        if len(changed) == 1 and not any(any(x) for x in d) and (flags >> changed[0]) & 1:
            j = changed[0]
            return dict(status='public_exception', key=P+j, old=ex[j], new=ex2[j])
        return dict(status='not_single_update')
    active = [i for i in range(2) if any(d[i])]
    if not active:
        return dict(status='no_change')
    keys = []
    for i in active:
        delta = d[i]
        if not n or not delta[-1]:
            return dict(status='not_single_update')
        k = -poly[0] % P if n == 1 else (delta[-2]*pow(delta[-1], -1, P)-poly[-2]) % P
        # Verify all coefficients of D*(X-k) = leading(D)*P.
        product = [0]*(n+1)
        for j, v in enumerate(delta):
            product[j] = (product[j]-k*v) % P
            product[j+1] = (product[j+1]+v) % P
        if product != [delta[-1]*v % P for v in poly] or evaluate(poly, k):
            return dict(status='not_single_update')
        keys.append(k)
    if len(set(keys)) != 1:
        return dict(status='not_single_update')
    k = keys[0]
    old = evaluate(lo, k)+P*evaluate(hi, k)
    new = evaluate(lo2, k)+P*evaluate(hi2, k)
    if max(old, new) >= 2**32:
        return dict(status='invalid_value')
    return dict(status='recovered', key=k, old=old, new=new, active_components=active,
                candidate_rule='P_only' if n == 1 else 'two_leading_deltas')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('before')
    parser.add_argument('after')
    args = parser.parse_args()
    t0 = time.perf_counter_ns()
    before, after = Path(args.before).read_bytes(), Path(args.after).read_bytes()
    t1 = time.perf_counter_ns()
    result = recover(before, after)
    t2 = time.perf_counter_ns()
    print(json.dumps(dict(**result, read_us=(t1-t0)/1000, analysis_us=(t2-t1)/1000)))
