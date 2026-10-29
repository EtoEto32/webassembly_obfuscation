"""Deterministic corpus, binary transformations, optimizers and binary-only attacks."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import traceback
import prototype as p
import recover


def kernels():
    v = lambda i: ('var', i)
    neg = lambda t: ('xor', t, ('const', p.MASK))
    def tree(leaves, ops):
        if len(leaves) == 1:
            return leaves[0]
        cut = len(leaves) // 2
        return (ops[len(leaves) % len(ops)], tree(leaves[:cut], ops), tree(leaves[cut:], ops))
    rng = random.Random(20261018)
    shuffled = list(range(24))
    rng.shuffle(shuffled)
    return {
        'ch': (3, ('xor', ('and', v(0), v(1)), ('and', neg(v(0)), v(2)))),
        'maj': (3, ('xor', ('xor', ('and', v(0), v(1)), ('and', v(0), v(2))), ('and', v(1), v(2)))),
        'mixed12': (12, tree([v(i) for i in range(12)] + [v(i) for i in (3, 0, 10, 7)], ['xor', 'or', 'and'])),
        'parity16': (16, tree([v(i) for i in range(16)], ['xor'])),
        'blend24': (24, tree([v(i) for i in shuffled], ['or', 'and'])),
    }


def mba(t):
    if t[0] in ('var', 'const'):
        return t
    a, b = mba(t[1]), mba(t[2])
    return ('xor', ('or', a, b), ('xor', a, b)) if t[0] == 'and' else (t[0], a, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('output', type=Path)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    report = {'status': 'building', 'python': platform.python_version(),
              'wabt': p.tool('wat2wasm', ['--version']).strip(),
              'binaryen': p.tool('wasm-opt', ['--version']).strip(), 'conditions': [], 'recovery': []}
    try:
        fixtures = {}
        for kernel, (n, t) in kernels().items():
            fixtures[kernel] = {'n': n, 'tree': t, 'role': 'known_negative_control' if kernel in ('ch', 'maj', 'parity16') else 'synthetic_formula'}
            for mode, formula in [('plain', t), ('mba', mba(t))]:
                wp = a.output / f'{kernel}-{mode}-raw.wat'
                wp.write_text(p.plain_wat(n, '"run"', formula), encoding='utf-8')
                p.tool('wat2wasm', [wp, '-o', wp.with_suffix('.wasm')])
            for mode, fraction in [('graph', 0), ('elim50', 0.5), ('elim80', 0.8)]:
                p.transform(a.output / f'{kernel}-plain-raw.wasm', a.output / f'{kernel}-{mode}-raw.wasm', fraction)
            for mode in ('plain', 'mba', 'graph', 'elim50', 'elim80'):
                for opt in ('raw', 'O2', 'O3'):
                    path = a.output / f'{kernel}-{mode}-{opt}.wasm'
                    if opt != 'raw':
                        p.tool('wasm-opt', [a.output / f'{kernel}-{mode}-raw.wasm', '-'+opt, '--enable-bulk-memory', '-o', path])
                    p.tool('wasm-validate', [path])
                    p.tool('wasm2wat', [path, '--fold-exprs', '-o', path.with_suffix('.dis.wat')])
                    report['conditions'].append({'kernel': kernel, 'mode': mode, 'opt': opt, 'file': path.name,
                                                 'bytes': path.stat().st_size, 'n': n,
                                                 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
                    out = a.output / 'recovered-v2' / path.name
                    try:
                        r = recover.recover(path, out)
                    except OverflowError as exc:
                        r = {'status': 'budget_exhausted', 'message': str(exc)}
                    except (ValueError, RuntimeError) as exc:
                        r = {'status': 'unsupported_or_error', 'message': str(exc)}
                    report['recovery'].append({'file': path.name, **r})
        report['status'] = 'built'
        (a.output / 'fixtures.json').write_text(json.dumps(fixtures, indent=2), encoding='utf-8')
        (a.output / 'recovery-v2.json').write_text(json.dumps({'reason': 'Corrected zero-filled-memory parser; initial pass in this fresh run.', 'results': report['recovery']}, indent=2), encoding='utf-8')
    except Exception:
        report['status'] = 'failed'
        report['error'] = traceback.format_exc()
        raise
    finally:
        (a.output / 'build.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        for name in ('plan.md', 'prototype.py', 'recover.py', 'build.py'):
            (a.output / ('source-' + name)).write_bytes((Path(__file__).parent / name).read_bytes())
        print(json.dumps({'status': report['status'], 'binaries': len(report['conditions']),
                          'recovery': {s: sum(r['status'] == s for r in report['recovery']) for s in set(r['status'] for r in report['recovery'])}}))


if __name__ == '__main__':
    main()
