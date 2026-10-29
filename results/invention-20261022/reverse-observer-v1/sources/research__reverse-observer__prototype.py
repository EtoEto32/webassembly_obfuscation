"""Restricted reverse-acceptance construction, with fully expanded Boolean encoding."""
import argparse
import importlib.util
import random
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('reverse_observer_tools', ROOT / 'research/isotope-swizzle/prototype.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)


def c(x): return f'(i32.const {x & 0xffffffff})'


def join(op, values, identity=0):
    values = list(values)
    if not values: return c(identity)
    result = values[0]
    for v in values[1:]: result = f'({op} {result} {v})'
    return result


def select_table(values):
    result = c(values[-1])
    for i in reversed(range(len(values)-1)):
        result = f'(select {c(values[i])} {result} (i32.eq (local.get 0) {c(i)}))'
    return result


def helper(expression):
    return f'(func (param i32) (result i32) {expression})'


def consumer(initial, reverse):
    if reverse:
        setup = '(local.set 3 (local.get 1))'
        before = '(br_if 1 (i32.eqz (local.get 3))) (local.set 3 (i32.sub (local.get 3) (i32.const 1)))'
        after = ''
    else:
        setup = '(local.set 3 (i32.const 0))'
        before = '(br_if 1 (i32.ge_u (local.get 3) (local.get 1)))'
        after = '(local.set 3 (i32.add (local.get 3) (i32.const 1)))'
    return f'''(func (export "run") (param i32 i32) (result i32) (local i32 i32)
       (if (i32.gt_u (local.get 1) (i32.const 32)) (then unreachable))
       (local.set 2 {c(initial)}) {setup}
       (block (loop {before}
         (local.set 2 (call_indirect (type 0) (local.get 2)
           (i32.and (i32.shr_u (local.get 0) (local.get 3)) (i32.const 1))))
         {after} (br 0)))
       (call_indirect (type 0) (local.get 2) (i32.const 2)))'''


def assemble(helpers, initial, reverse):
    return '(module (type (func (param i32) (result i32))) (table 3 3 funcref) ' + ' '.join(helpers) + ' ' + consumer(initial, reverse) + ' (elem (i32.const 0) func 0 1 2))'


def source(delta, accept):
    hs = [helper(select_table([row[a] for row in delta])) for a in (0, 1)]
    hs.append(helper(f'(i32.and (i32.shr_u {c(accept)} (local.get 0)) (i32.const 1))'))
    return assemble(hs, 0, False)


def parse(src):
    mod = q.read(src)
    fs = [x for x in mod[1:] if x[0] == 'func']
    if len(fs) != 4: raise ValueError('four functions required')
    def body(f):
        rows = [e for e in f[1:] if e[0] not in ('type', 'param', 'result', 'local')]
        if len(rows) != 1: raise ValueError('table helper')
        return rows[0]
    def table(e):
        result = []
        while e[0] == 'select':
            if e[1][0] != 'i32.const' or e[3] != ['i32.eq', ['local.get', '0'], ['i32.const', str(len(result))]]:
                raise ValueError('canonical transition select')
            result.append(int(e[1][1], 0)); e = e[2]
        if e[0] != 'i32.const': raise ValueError('table end')
        result.append(int(e[1], 0)); return result
    a, b = table(body(fs[0])), table(body(fs[1]))
    n = len(a)
    if n != len(b) or not 3 <= n <= 10 or any(v < 0 or v >= n for v in a+b):
        raise ValueError('3..10 state DFA')
    ob = body(fs[2])
    if ob[0] != 'i32.and' or ob[2] != ['i32.const', '1'] or ob[1][0] != 'i32.shr_u' or ob[1][2] != ['local.get', '0']:
        raise ValueError('acceptance mask')
    accept = int(ob[1][1][1], 0)
    if not 0 < accept < (1 << n): raise ValueError('nonempty acceptance mask')
    delta = list(map(list, zip(a, b)))
    with tempfile.TemporaryDirectory(dir=ROOT / 'tmp', prefix='reverse-observer-') as td:
        ref = Path(td) / 'reference.wasm'; q.compile(source(delta, accept), ref)
        if q.read(ref) != mod: raise ValueError('source outside exact profile')
    return delta, accept


def gates(n, seed):
    r = random.Random(seed)
    return [tuple(r.sample(range(n), 3)) for _ in range(2*n)]


def encode(value, gs):
    for i, j, k in gs: value ^= (((value >> j) & 1) & ((value >> k) & 1)) << i
    return value


def coefficients(values):
    values = list(values); size = len(values)
    for bit in range(size.bit_length()-1):
        for mask in range(size):
            if mask & (1 << bit): values[mask] ^= values[mask ^ (1 << bit)]
    return values


def anf(values):
    coeff = coefficients(values); terms = []
    for monomial, value in enumerate(coeff):
        if not value: continue
        if not monomial: terms.append(c(value)); continue
        factors = [f'(i32.and (i32.shr_u (local.get 0) {c(i)}) (i32.const 1))'
                   for i in range(monomial.bit_length()) if monomial & (1 << i)]
        term = join('i32.and', factors, 1)
        terms.append(f'(i32.and {c(value)} (i32.sub (i32.const 0) {term}))')
    return helper(join('i32.xor', terms)), sum(v != 0 for v in coeff)


def transformed(delta, accept, mode, seed):
    n = len(delta); gs = gates(n, seed) if mode == 'mixed' else []
    rows = [[], [], []]
    for z in range(1 << n):
        v = encode(z, reversed(gs))
        for a in (0, 1):
            u = sum(((v >> delta[i][a]) & 1) << i for i in range(n))
            rows[a].append(encode(u, gs))
        rows[2].append(v & 1)
    hs, term_counts = zip(*(anf(values) for values in rows))
    return assemble(hs, encode(accept, gs), True), dict(n=n, term_counts=term_counts, gates=gs)


def transform(src, dst, mode='mixed', seed=221011):
    start = time.perf_counter(); delta, accept = parse(src)
    if mode not in ('reverse', 'mixed'): raise ValueError('mode')
    wat, info = transformed(delta, accept, mode, seed)
    q.compile(wat, dst)
    return dict(mode=mode, seed=seed, **info, transform_ms=(time.perf_counter()-start)*1000)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('source'); ap.add_argument('output')
    ap.add_argument('--mode', choices=['reverse', 'mixed'], default='mixed'); ap.add_argument('--seed', type=int, default=221011)
    a = ap.parse_args(); q.save(str(a.output)+'.json', transform(a.source, a.output, a.mode, a.seed))
