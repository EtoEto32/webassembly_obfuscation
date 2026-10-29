"""Enumerate loss compatibility independently by all small state pairs."""
import argparse
import itertools
from pathlib import Path
import prototype as p


def run(out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    n = 3
    profiles = [[(1, 0, 1), (2, 1, 1)],
                [(0, 1, 2), (1, 0, 2)],
                [(2, 0, 1), (0, 1, 1), (1, 2, 1)]]
    rows, pair_checks, witness = [], 0, None
    values = [bytes(v) for v in itertools.product(range(2), repeat=n)]
    for ops in profiles:
        accepted, commuting, checked = 0, 0, 0
        for flat in range(1 << (n * n)):
            b = [(flat >> (n * i)) & ((1 << n) - 1) for i in range(n)]
            inv = p.m.inverse(b)
            if inv is None:
                continue
            checked += 1
            ps = p.prefixes(n, ops)
            compatible = True
            for prefix in ps:
                desired = p.m.product(p.m.product(b, prefix), inv)
                for x in values:
                    for y in values:
                        pair_checks += 1
                        same_current = p.m.apply(prefix, x) == p.m.apply(prefix, y)
                        same_desired = p.m.apply(desired, x) == p.m.apply(desired, y)
                        if same_current and not same_desired:
                            compatible = False
                            if witness is None:
                                witness = dict(b=b, prefix=prefix, x=list(x), y=list(y),
                                               current=list(p.m.apply(prefix, x)),
                                               desired_x=list(p.m.apply(desired, x)),
                                               desired_y=list(p.m.apply(desired, y)))
            death = p.deaths(n, ps)
            flag = all(death[k] >= death[i] for i, row in enumerate(inv) for k in p.m.bits(row))
            if flag != compatible:
                raise AssertionError('flag condition mismatch')
            if compatible:
                accepted += 1
                info = p.plan(n, ops, b)
                for j, prefix in enumerate(ps):
                    for x in values:
                        cur = p.m.apply(prefix, x)
                        delta = p.m.apply(info['repairs'][j]['correction'], cur)
                        got = bytes(a ^ v for a, v in zip(cur, delta))
                        want = p.m.apply(p.m.product(p.m.product(b, prefix), inv), x)
                        assert got == want
                commuting += int(info['commuting_copies'] == len(ops))
        rows.append(dict(ops=ops, invertible_checked=checked, compatible=accepted,
                         commuting_with_all=commuting))
    assert witness is not None
    out.parent.mkdir(parents=True, exist_ok=True)
    p.q.save(out, dict(rows=rows, state_pair_checks=pair_checks, impossible_without_history=witness))
    print({'profiles': len(rows), 'state_pair_checks': pair_checks, 'rows': rows})


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('output')
    run(ap.parse_args().output)
