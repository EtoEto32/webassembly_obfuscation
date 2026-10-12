import hashlib
import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def partitions(n):
    def visit(labels, top):
        if len(labels) == n:
            yield tuple(labels)
        else:
            for label in range(top + 2):
                yield from visit(labels + [label], max(top, label))
    yield from visit([0], 0)


def binary_quotient(labels, op):
    table = {}
    for x in range(len(labels)):
        for y in range(len(labels)):
            key = (labels[x], labels[y])
            value = labels[op(x, y)]
            if key in table and table[key] != value:
                return False
            table[key] = value
    return True


def unary_quotient(labels, op):
    table = {}
    for x in range(len(labels)):
        key, value = labels[x], labels[op(x)]
        if key in table and table[key] != value:
            return False
        table[key] = value
    return True


def rotr(x, r, w):
    r %= w
    return ((x >> r) | (x << (w-r))) & ((1 << w)-1)


def main():
    output = ROOT / 'results.json'
    if output.exists():
        raise FileExistsError(output)
    small = []
    for w in (1, 2, 3):
        n = 1 << w
        accepted = {name: [] for name in ('add', 'xor', 'rotate', 'add_rotate')}
        count = 0
        for labels in partitions(n):
            count += 1
            add = binary_quotient(labels, lambda x,y: (x+y) % n)
            xor = binary_quotient(labels, lambda x,y: x^y)
            rotate = unary_quotient(labels, lambda x: rotr(x,1,w))
            for name, passed in [('add',add),('xor',xor),('rotate',rotate),('add_rotate',add and rotate)]:
                if passed:
                    accepted[name].append(labels)
        expected = {tuple(x % (1 << k) for x in range(n)) for k in range(w+1)}
        assert set(accepted['add']) == expected
        assert set(accepted['add_rotate']) == {tuple([0]*n), tuple(range(n))}
        small.append(dict(width=w, partitions=count, counts={k:len(v) for k,v in accepted.items()},
                          accepted=accepted))
    assert [s['partitions'] for s in small] == [2,15,4140]
    specs = {'Sigma0': ((2,13,22),None), 'Sigma1': ((6,11,25),None),
             'sigma0': ((7,18),3), 'sigma1': ((17,19),10)}
    witnesses = []
    for name, (rotations, shift) in specs.items():
        def op(x):
            value = 0
            for r in rotations:
                value ^= rotr(x,r,32)
            if shift is not None:
                value ^= x >> shift
            return value
        for k in range(1,32):
            mask = (1 << k)-1
            for j in range(k,32):
                x, y = 0, 1 << j
                if (op(x) & mask) != (op(y) & mask):
                    assert (x & mask) == (y & mask)
                    witnesses.append(dict(operation=name,k=k,x=x,y=y,fx=op(x),fy=op(y),
                                          projected_fx=op(x)&mask, projected_fy=op(y)&mask))
                    break
            else:
                raise AssertionError((name,k))
    result = dict(python=platform.python_version(), small=small, witnesses=witnesses,
                  witness_count=len(witnesses),
                  hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['check.py','protocol.json']})
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(small=[{k:v for k,v in s.items() if k!='accepted'} for s in small],
                          witness_count=len(witnesses)), indent=2))


if __name__ == '__main__':
    main()
