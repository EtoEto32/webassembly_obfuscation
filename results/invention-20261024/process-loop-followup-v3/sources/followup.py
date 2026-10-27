"""Serial schedules and native i32 witnesses; does not transform user programs."""
import argparse
from collections import Counter
import hashlib
from itertools import permutations, product
import json
from pathlib import Path
import random
import shutil
import subprocess
import check as m


def schedules():
    maps = list(product(range(2), repeat=2))
    result = []
    for order in permutations(range(3)):
        periods = Counter()
        max_prefix = 0
        witness = None
        for fs in product(maps, repeat=3):
            t = []
            for s in range(8):
                x = list(m.unpack(s, 1))
                for j in order:
                    x[j] = m.wiring(tuple(fs[k][x[k]] for k in range(3)), 1)[j]
                t.append(m.pack(x, 1))
            for s in range(8):
                prefix, cycle = m.cycles_from(t, s)
                periods[len(cycle)] += 1
                max_prefix = max(max_prefix, len(prefix))
                if len(cycle) > 1 and witness is None:
                    witness = {'maps': fs, 'start': s, 'prefix': prefix, 'cycle': cycle}
        result.append({'order': order, 'period_histogram': dict(periods),
                       'max_prefix_sweeps': max_prefix, 'witness': witness})
    return result


def anf2(table, bit):
    a = [(v >> bit) & 1 for v in table]
    for k in range(2):
        for j in range(4):
            if j & (1 << k):
                a[j] ^= a[j ^ (1 << k)]
    return a


def pair_expr(table, arg):
    mask = '(i32.const 1431655765)'
    lo = f'(i32.and {arg} {mask})'
    hi = f'(i32.and (i32.shr_u {arg} (i32.const 1)) {mask})'
    basis = [mask, lo, hi, f'(i32.and {lo} {hi})']
    vals = []
    for bit in range(2):
        terms = [expr for use, expr in zip(anf2(table, bit), basis) if use]
        v = terms[0] if terms else '(i32.const 0)'
        for expr in terms[1:]:
            v = f'(i32.xor {v} {expr})'
        vals.append(v)
    return f'(i32.or {vals[0]} (i32.shl {vals[1]} (i32.const 1)))'


def pair_apply(table, x):
    return sum(table[(x >> k) & 3] << k for k in range(0, 32, 2))


def wiring_wat(a):
    return [f'(i32.and {a[l]} (i32.xor {a[r]} (i32.const -1)))'
            for l, r in ((2, 1), (0, 2), (1, 0))]


def pair_wat(fs):
    lines = [f'(local.set {j+3} {pair_expr(fs[j], f"(local.get {j})")})' for j in range(3)]
    return '(module (func (export "step") (param i32 i32 i32) (result i32 i32 i32) (local i32 i32 i32) ' + ' '.join(lines + wiring_wat([f'(local.get {j+3})' for j in range(3)])) + '))'


def solver_wat(mode='enumerate'):
    # p,q,r for each local map, then the three initial words, then family.
    get = lambda j: f'(local.get {j})'
    functions = []
    for j in range(3):
        a, b, c, x, family = [f'(local.get {k})' for k in range(5)]
        affine = f'(i32.add (i32.mul {a} {x}) {b})'
        quadratic = f'(i32.add (i32.add (i32.mul {a} (i32.mul {x} {x})) (i32.mul {b} {x})) {c})'
        xor_add = f'(i32.add (i32.xor (i32.add {x} {a}) {b}) (i32.mul {c} {x}))'
        body = f'(if (result i32) (i32.eqz {family}) (then {affine}) (else (if (result i32) (i32.eq {family} (i32.const 1)) (then {quadratic}) (else {xor_add}))))'
        functions.append(f'(func $f{j} (param i32 i32 i32 i32 i32) (result i32) {body})')
    calls = [f'(call $f{j} {get(3*j)} {get(3*j+1)} {get(3*j+2)} (local.get $c{j}) {get(12)})'
             for j in range(3)]
    evaluate = ' '.join(f'(local.set $z{j} {calls[j]})' for j in range(3))
    updates = wiring_wat([f'(local.get $z{j})' for j in range(3)])
    candidates = ' '.join(
        f'(local.set $c{j} (i32.or (i32.and {get(9+j)} (i32.xor (local.get $bit) (i32.const -1))) '
        f'(i32.mul (i32.and (i32.shr_u (local.get $choice) (i32.const {j})) (i32.const 1)) (local.get $bit))))'
        for j in range(3))
    diffs = [f'(i32.xor {updates[j]} (local.get $c{j}))' for j in range(3)]
    diff = f'(i32.or {diffs[0]} (i32.or {diffs[1]} {diffs[2]}))'
    save = ' '.join(f'(local.set $r{j} (local.get $c{j}))' for j in range(3))
    commit = ' '.join(f'(local.set {9+j} (local.get $r{j}))' for j in range(3))
    loop = f'''(local.set $choice (i32.const 0)) (local.set $n (i32.const 0))
          (loop $choices {candidates} {evaluate}
            (if (i32.eqz (i32.and {diff} (local.get $bit)))
              (then {save} (local.set $n (i32.add (local.get $n) (i32.const 1)))))
            (local.set $choice (i32.add (local.get $choice) (i32.const 1)))
            (br_if $choices (i32.lt_u (local.get $choice) (i32.const 8))))
          (if (i32.ne (local.get $n) (i32.const 1)) (then unreachable))'''
    if mode == 'zero':
        clear = ' '.join(f'(local.set $c{j} (i32.and {get(9+j)} (i32.xor (local.get $bit) (i32.const -1))))' for j in range(3))
        place = ' '.join(f'(local.set $r{j} (i32.or (local.get $c{j}) (i32.and {updates[j]} (local.get $bit))))' for j in range(3))
        loop = clear + ' ' + evaluate + ' ' + place
    elif mode != 'enumerate':
        raise ValueError(mode)
    return f'''(module {' '.join(functions)}
      (func (export "solve") (param {' '.join(['i32']*13)}) (result i32 i32 i32)
        (local $bit i32) (local $choice i32) (local $c0 i32) (local $c1 i32) (local $c2 i32)
        (local $r0 i32) (local $r1 i32) (local $r2 i32) (local $n i32)
        (local $z0 i32) (local $z1 i32) (local $z2 i32)
        (local.set $bit (i32.const 1))
        (loop $bits
          {loop}
          {commit}
          (local.set $bit (i32.shl (local.get $bit) (i32.const 1)))
          (br_if $bits (local.get $bit)))
        {get(9)} {get(10)} {get(11)}))'''


def compile_pair(out, name, text):
    src = out / (name + '.wat')
    src.write_text(text, encoding='utf-8')
    raw, opt = src.with_suffix('.wasm'), out / (name+'-O3.wasm')
    m.w.tool('wat2wasm', [src, '-o', raw])
    m.w.tool('wasm-opt', [raw, '-O3', '--enable-multivalue', '-o', opt])
    for p in (raw, opt):
        m.w.tool('wasm-validate', [p])
    return [raw.name, opt.name]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('main', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    source = json.loads((args.main/'results.json').read_text(encoding='utf-8'))
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    schedule = schedules()
    assert all(s['period_histogram'] == {1: 506, 2: 6} for s in schedule)
    solver_files = compile_pair(out, 'congruent-solver', solver_wat())
    solver_files += compile_pair(out, 'zero-solver', solver_wat('zero'))
    zero_identity_checks = []
    for fs in product(list(product(range(2), repeat=2)), repeat=3):
        t = m.transition(fs, 1)
        root = t[0]
        assert t[root] == root and [i for i, j in enumerate(t) if i == j] == [root]
        zero_identity_checks.append({'maps': fs, 'root': root})
    rng = random.Random(20261024)
    solver_cases = []
    for c in source['congruence']['width32_cases']:
        initials = [[0]*3, [0xffffffff]*3, [1, 2, 4], [rng.getrandbits(32) for _ in range(3)]]
        family = ('affine', 'quadratic', 'xor_add').index(c['family'])
        for initial in initials:
            inp = sum(c['coefficients'], []) + initial + [family]
            solver_cases.append({'input': inp, 'expected': c['solution']})
    pair_cases = []
    for label, case in source['two_bit_permutations']['witnesses'].items():
        files = compile_pair(out, 'pair-'+label, pair_wat(case['maps']))
        inputs = [[0]*3, [0xffffffff]*3, [0x55555555]*3, [0xaaaaaaaa]*3]
        inputs += [[rng.getrandbits(32) for _ in range(3)] for _ in range(1024)]
        # Repeat each small fixed point across every 2bit lane.
        roots = [[v*0x55555555 for v in m.unpack(s, 2)] for s in case['roots']]
        inputs += roots
        checks = [{'input': x, 'expected': m.wiring(tuple(pair_apply(case['maps'][j], x[j]) for j in range(3)), 0xffffffff)} for x in inputs]
        pair_cases.append({'label': label, 'files': files, 'maps': case['maps'],
                           'small_roots': case['roots'], 'example_word_roots': roots,
                           'word_root_count_by_cartesian_product': len(case['roots'])**16,
                           'checks': checks})
    payload = {'schedules': schedule, 'algorithm': 'lower bits: enumerate 8 candidates and direct zero-context rule',
               'zero_identity_checks': zero_identity_checks,
               'solver_files': solver_files, 'solver_cases': solver_cases, 'pair_cases': pair_cases,
               'scope': 'construction checks, not a new source-to-obfuscated-program compiler'}
    (out/'cases.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    r = subprocess.run(['node', str(Path(__file__).with_name('followup.cjs')), str(out)],
                       capture_output=True, text=True, timeout=30)
    (out/'node-stdout.txt').write_text(r.stdout, encoding='utf-8')
    (out/'node-stderr.txt').write_text(r.stderr, encoding='utf-8')
    if r.returncode:
        raise RuntimeError(r.stderr)
    report = json.loads(r.stdout)
    (out/'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    snapshots = out/'sources'
    snapshots.mkdir()
    for name in ('check.py', 'followup.py', 'followup.cjs', 'plan.md'):
        shutil.copy2(Path(__file__).with_name(name), snapshots/name)
    shutil.copy2(m.ROOT/'research/connectivity-elimination/prototype.py', snapshots/'wasm-helper.py')
    hashes = {str(f.relative_to(out)).replace('\\', '/'): hashlib.sha256(f.read_bytes()).hexdigest()
              for f in sorted(out.rglob('*')) if f.is_file()}
    (out/'sha256.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(out), 'schedules': schedule,
                      'wasm': report, 'hashed_files': len(hashes)}))


if __name__ == '__main__':
    main()
