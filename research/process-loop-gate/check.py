"""Feasibility screen, not an obfuscator. Standard library only."""
import argparse
from collections import Counter
import hashlib
import importlib.util
from itertools import permutations, product
import json
from pathlib import Path
import platform
import random
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    'wasm_helpers', ROOT / 'research/connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def wiring(a, mask):
    a, b, c = a
    return (c & (~b & mask), a & (~c & mask), b & (~a & mask))


def unpack(s, bits):
    mask = (1 << bits) - 1
    return tuple((s >> (bits * j)) & mask for j in range(3))


def pack(x, bits):
    return sum(v << (bits * j) for j, v in enumerate(x))


def mapping(fs, bits):
    mask = (1 << bits) - 1
    return [pack(wiring(tuple(fs[j][x[j]] for j in range(3)), mask), bits)
            for x in product(range(1 << bits), repeat=3)]


def transition(fs, bits):
    # Numeric state ordering, deliberately distinct from itertools product order.
    mask = (1 << bits) - 1
    return [pack(wiring(tuple(fs[j][v] for j, v in enumerate(unpack(s, bits))), mask), bits)
            for s in range(1 << (bits * 3))]


def cycles_from(t, start):
    seen, path = {}, []
    s = start
    while s not in seen:
        seen[s] = len(path)
        path.append(s)
        s = t[s]
    return path[:seen[s]], path[seen[s]:]


def scan(maps, bits, with_dynamics=False):
    hist, periods = Counter(), Counter()
    witnesses = {}
    cases = 0
    for fs in product(maps, repeat=3):
        t = transition(fs, bits)
        roots = [i for i, j in enumerate(t) if i == j]
        hist[len(roots)] += 1
        cases += 1
        key = 'zero' if not roots else ('multiple' if len(roots) > 1 else None)
        if key and key not in witnesses:
            witnesses[key] = {'maps': fs, 'roots': roots, 'transition': t}
        if with_dynamics:
            for s in range(len(t)):
                prefix, cycle = cycles_from(t, s)
                periods[len(cycle)] += 1
                if len(cycle) > 1 and 'cycle' not in witnesses:
                    witnesses['cycle'] = {'maps': fs, 'roots': roots, 'start': s,
                                          'prefix': prefix, 'cycle': cycle, 'transition': t}
    return {'maps': len(maps), 'cases': cases, 'fixed_point_histogram': dict(hist),
            'entry_period_histogram': dict(periods), 'witnesses': witnesses}


def solve_lower_bits(fs, bits):
    """Requires each f to preserve equality modulo 2**k, for every k."""
    mask = (1 << bits) - 1
    x = [0, 0, 0]
    for k in range(bits):
        matches = []
        for digits in product(range(2), repeat=3):
            candidate = [x[j] | (digits[j] << k) for j in range(3)]
            y = wiring(tuple(fs[j](candidate[j]) & mask for j in range(3)), mask)
            if all(((y[j] >> k) & 1) == digits[j] for j in range(3)):
                matches.append(candidate)
        if len(matches) != 1:
            raise ValueError('bit restriction does not have a unique solution')
        x = matches[0]
    if tuple(x) != wiring(tuple(fs[j](x[j]) & mask for j in range(3)), mask):
        raise ValueError('result is not a fixed point; locality precondition may be false')
    return tuple(x)


def congruence_checks():
    maps = [(p, q, tuple((p + q*x) & 3 for x in range(4)))
            for p in range(4) for q in range(4)]
    hist, mismatches = Counter(), []
    for triple in product(maps, repeat=3):
        t = transition([item[2] for item in triple], 2)
        roots = [i for i, j in enumerate(t) if i == j]
        hist[len(roots)] += 1
        got = solve_lower_bits([lambda x, p=p, q=q: p + q*x for p, q, _ in triple], 2)
        if roots != [pack(got, 2)]:
            mismatches.append(triple)
    rng = random.Random(20261023)
    wide = []
    for family in ('affine', 'quadratic', 'xor_add'):
        for _ in range(64):
            coefficients = [[rng.getrandbits(32) for _ in range(3)] for _ in range(3)]
            if family == 'affine':
                fs = [lambda x, a=a, b=b: a*x+b for a, b, c in coefficients]
            elif family == 'quadratic':
                fs = [lambda x, a=a, b=b, c=c: a*x*x+b*x+c for a, b, c in coefficients]
            else:
                fs = [lambda x, a=a, b=b, c=c: ((x+a) ^ b)+c*x for a, b, c in coefficients]
            before = time.perf_counter_ns()
            solved = solve_lower_bits(fs, 32)
            elapsed = (time.perf_counter_ns() - before)/1e6
            wide.append({'family': family, 'coefficients': coefficients,
                         'solution': solved, 'solver_ms': elapsed})
    assert not mismatches
    return {'width2_cases': 16**3, 'fixed_point_histogram': dict(hist),
            'solver_mismatches': mismatches, 'width32_cases': wide,
            'local_evaluations_per_width32_solution': 3*8*32,
            'timing_scope': 'single Python invocation per case, no performance claim'}


def wat(fs, bits):
    mask = (1 << bits) - 1
    lines = []
    for j, f in enumerate(fs):
        table = sum(v << (bits*i) for i, v in enumerate(f))
        arg = f'(i32.and (i32.shr_u (local.get 0) (i32.const {j*bits})) (i32.const {mask}))'
        lookup = f'(i32.and (i32.shr_u (i32.const {table}) (i32.mul {arg} (i32.const {bits}))) (i32.const {mask}))'
        lines.append(f'(local.set {j+1} {lookup})')
    vals = []
    for j, left, inverted in ((0, 3, 2), (1, 1, 3), (2, 2, 1)):
        term = f'(i32.and (local.get {left}) (i32.xor (local.get {inverted}) (i32.const {mask})))'
        vals.append(f'(i32.shl {term} (i32.const {bits*j}))')
    result = f'(i32.or {vals[0]} (i32.or {vals[1]} {vals[2]}))'
    return f'''(module
      (func $step (export "step") (param i32) (result i32) (local i32 i32 i32)
        {' '.join(lines)} {result})
      (func (export "count") (result i32) (local $i i32) (local $n i32)
        (loop $scan
          (local.set $n (i32.add (local.get $n) (i32.eq (local.get $i) (call $step (local.get $i)))))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br_if $scan (i32.lt_u (local.get $i) (i32.const {1 << (3*bits)}))))
        (local.get $n)))'''


def wasm_check(out, cases):
    entries = []
    for label, bits, case in cases:
        src = out / (label + '.wat')
        src.write_text(wat(case['maps'], bits), encoding='utf-8')
        raw = src.with_suffix('.wasm')
        w.tool('wat2wasm', [src, '-o', raw])
        opt = out / (label + '-O3.wasm')
        w.tool('wasm-opt', [raw, '-O3', '-o', opt])
        for path in (raw, opt):
            w.tool('wasm-validate', [path])
            interp = w.tool('wasm-interp', [path, '--run-all-exports'])
            (out / (path.stem + '-interp.txt')).write_text(interp, encoding='utf-8')
            assert 'count() => i32:' + str(len(case['roots'])) in interp
            entries.append({'file': path.name, 'expected': case['transition'],
                            'roots': case['roots'], 'wasm_bytes': path.stat().st_size})
    (out / 'wasm-cases.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
    r = subprocess.run(['node', str(Path(__file__).with_name('check.cjs')), str(out)],
                       text=True, capture_output=True, timeout=30)
    (out / 'node-stdout.txt').write_text(r.stdout, encoding='utf-8')
    (out / 'node-stderr.txt').write_text(r.stderr, encoding='utf-8')
    if r.returncode:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('output', type=Path)
    out = p.parse_args().output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter_ns()
    one = scan(list(product(range(2), repeat=2)), 1, True)
    two = scan(list(permutations(range(4))), 2)
    congruence = congruence_checks()
    assert one['fixed_point_histogram'] == {1: 64}
    assert 'cycle' in one['witnesses']
    assert {'zero', 'multiple'} <= set(two['witnesses'])
    cases = [('one-cycle', 1, one['witnesses']['cycle'])]
    cases += [('two-' + key, 2, two['witnesses'][key]) for key in ('zero', 'multiple')]
    identity = [[0, 1, 2, 3]]*3
    t = transition(identity, 2)
    cases.append(('two-identity', 2, {'maps': identity, 'transition': t,
                                    'roots': [i for i, j in enumerate(t) if i == j]}))
    wasm = wasm_check(out, cases)
    summary = {'one_bit': one, 'two_bit_permutations': two,
               'congruence': congruence, 'wasm': wasm,
               'total_wall_ms': (time.perf_counter_ns()-started)/1e6,
               'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                               'node': subprocess.check_output(['node', '--version'], text=True).strip()},
               'scope': 'feasibility gate; not a semantics-preserving general Wasm obfuscator'}
    (out / 'results.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    snapshot = out / 'sources'
    snapshot.mkdir()
    for name in ('check.py', 'check.cjs', 'plan.md'):
        shutil.copy2(Path(__file__).with_name(name), snapshot / name)
    shutil.copy2(ROOT / 'research/connectivity-elimination/prototype.py', snapshot / 'wasm-helper.py')
    hashes = {str(f.relative_to(out)).replace('\\', '/'): hashlib.sha256(f.read_bytes()).hexdigest()
              for f in sorted(out.rglob('*')) if f.is_file()}
    (out / 'sha256.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(out), 'one_histogram': one['fixed_point_histogram'],
                      'two_histogram': two['fixed_point_histogram'], 'wasm': wasm,
                      'hashed_files': len(hashes)}))


if __name__ == '__main__':
    main()
