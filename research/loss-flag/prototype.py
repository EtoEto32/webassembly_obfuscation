"""Current-state repair for copy-compatible loss flags; a restricted experiment."""
import argparse
import importlib.util
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


base = module('loss_flag_base', ROOT / 'research/prefix-repair/prototype.py')
q, m = base.q, base.m


def prefixes(n, ops):
    out = [m.ident(n)]
    for op in ops:
        if op[2] <= 0:
            raise ValueError('positive copy length required')
        out.append(m.product(m.matrix(n, op), out[-1]))
    return out


def deaths(n, ps):
    result = [len(ps)] * n
    for j, p in enumerate(ps):
        survivors = set(row.bit_length() - 1 for row in p)
        for i in range(n):
            if i not in survivors and result[i] == len(ps):
                result[i] = j
    return result


def encoding(n, ops, seed):
    death = deaths(n, prefixes(n, ops))
    allowed = [(i, k) for i in range(n) for k in range(n)
               if i != k and death[k] >= death[i]]
    rng, inv = random.Random(seed), m.ident(n)
    for _ in range(3 * n):
        if allowed:
            i, k = rng.choice(allowed)
            inv[i] ^= inv[k]
    b = m.inverse(inv)
    assert b is not None
    return b


def plan(n, ops, b):
    old = base.plan(n, ops, b)
    ps = prefixes(n, ops)
    repairs = []
    for j, prefix in enumerate(ps):
        # For each surviving original byte, select one of its current copies.
        reps = {}
        for pos, row in enumerate(prefix):
            reps.setdefault(row.bit_length() - 1, pos)
        side = [1 << reps[i] if i in reps else 0 for i in range(n)]
        delta = old['delta'][j]
        w = m.product(delta, side)
        if m.product(w, prefix) != delta:
            raise ValueError('encoding destroys information required at prefix ' + str(j))
        v = base.basis(w)
        u = base.coordinates(w, v)
        repairs.append(dict(v=v, u=u, rank=len(v), correction=w))
    return dict(**old, death=deaths(n, ps), repairs=repairs,
                entry_saved_bytes=0, repair_temporary_values=max(r['rank'] for r in repairs),
                commuting_copies=sum(m.product(b, m.matrix(n, op)) ==
                                     m.product(m.matrix(n, op), b) for op in ops))


def wat(data, ops, b=None, mode='plain'):
    b = b if b is not None else m.ident(len(data))
    if mode in ('plain', 'eager', 'basis'):
        return base.wat(data, ops, b, mode)
    if mode not in ('current', 'bad'):
        raise ValueError('unknown mode')
    info = plan(len(data), ops, b)
    parts = []
    def fix(j):
        r = info['repairs'][j]
        return base.snapshot(r['v']) + ' ' + base.patch(r['u'])
    for j, op in enumerate(ops):
        if mode == 'current' and j:
            parts.append(f'(if (i32.eq (local.get 0) {base.c(j)}) (then {fix(j)}))')
        parts.append(base.rawcopy(op, j))
    parts.append(fix(len(ops)))
    locals_ = info['repair_temporary_values']
    local_text = '(local ' + ' '.join(['i32'] * locals_) + ')' if locals_ else ''
    run = '(func (export "run") (param i32) ' + local_text + ' ' + ' '.join(parts) + ')'
    digest = ['(local.set 0 ' + base.c(2166136261) + ')']
    for row in info['inverse']:
        digest.append(f'(local.set 0 (i32.mul (i32.xor (local.get 0) {base.linear(row, base.load)}) {base.c(16777619)}))')
    observe = '(func (export "digest") (result i32) (local i32) ' + ' '.join(digest) + ' (local.get 0))'
    return '(module (memory 1 1) ' + run + observe + ' (data (i32.const 0) "' + base.blob(m.apply(b, data)) + '"))'


def transform(src, dst, mode='current', seed=221001):
    start = time.perf_counter()
    data, ops = base.parse(src)
    b = encoding(len(data), ops, seed)
    info = plan(len(data), ops, b)
    q.compile(wat(data, ops, b, mode), dst)
    return dict(n=len(data), ops=ops, mode=mode, seed=seed, **info,
                transform_ms=(time.perf_counter() - start) * 1000)


def recovery():
    # Load the existing attacker unchanged, binding its old dependency explicitly.
    saved = sys.modules.get('prototype')
    try:
        sys.modules['prototype'] = base
        return module('loss_flag_existing_attacker', ROOT / 'research/prefix-repair/recover.py')
    finally:
        if saved is None:
            del sys.modules['prototype']
        else:
            sys.modules['prototype'] = saved


def bench(src, dst):
    mod = q.read(src)
    mod.append(q.w.parse('''(module
      (func (export "bench") (param i32) (result i32) (local i32)
        (block (loop
          (br_if 1 (i32.eqz (local.get 0)))
          (call 0 (i32.const -1))
          (local.set 0 (i32.sub (local.get 0) (i32.const 1))) (br 0)))
        (call 1)))''')[1])
    q.compile(q.w.emit(mod), dst)


def safe(value):
    if isinstance(value, int) and abs(value) >= 2**53:
        return str(value)
    if isinstance(value, list):
        return [safe(x) for x in value]
    if isinstance(value, tuple):
        return [safe(x) for x in value]
    if isinstance(value, dict):
        return {k: safe(v) for k, v in value.items()}
    return value


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('output')
    ap.add_argument('--mode', choices=['eager', 'basis', 'current'], default='current')
    ap.add_argument('--seed', type=int, default=221001)
    args = ap.parse_args()
    q.save(str(args.output) + '.json', safe(transform(args.source, args.output, args.mode, args.seed)))
