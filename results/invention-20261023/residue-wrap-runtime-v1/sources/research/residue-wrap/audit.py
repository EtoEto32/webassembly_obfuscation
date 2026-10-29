"""Independent interpreter probes, byte replay, and projector rejection controls."""
import ast
import json
from pathlib import Path
import sys
import prototype as p


def reference(e, a, b):
    if e[0] == 'p': return (a, b)[e[1]]
    if e[0] == 'c': return e[1] & p.MASK
    x, y = reference(e[1], a, b), reference(e[2], a, b)
    return {'add': lambda: x+y, 'sub': lambda: x-y, 'mul': lambda: x*y}[e[0]]() & p.MASK


def interpret(src, pairs, dst):
    m = p.q.read(src)
    index = next(x[2][1] for x in m[1:] if x[0] == 'export' and x[1] == '"run"')
    probes = ['(func (export "probe%d") (result i32) (call %s (i32.const %d) (i32.const %d)))' % (i, index, a, b)
              for i, (a, b) in enumerate(pairs)]
    p.q.compile(p.q.w.emit(m)[:-1] + ''.join(probes) + ')', dst)
    log = p.q.w.tool('wasm-interp', [dst, '--run-all-exports'])
    dst.with_suffix('.log').write_text(log, encoding='utf-8')
    values = []
    for line in log.splitlines():
        if not line.startswith('probe'): continue
        if 'i32:' not in line: raise AssertionError(line)
        values.append(int(line.split('i32:')[1]))
    if len(values) != len(pairs): raise AssertionError('missing probe')
    return values


def main(main_dir, dest):
    source = Path(main_dir).resolve(); out = Path(dest).resolve(); out.mkdir(parents=True, exist_ok=False)
    cases = json.loads((source/'cases.json').read_text(encoding='utf-8'))
    manifest = json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    pairs = [(0, 0), (1, 0), (0, 1), (65537, 65539), (0xffffffff, 1),
             (0xffffffff, 0xffffffff), (0x80000000, 0x7fffffff), (0, 0xffffffff)]
    rows = []; replay = []; identities = []
    for row in manifest:
        f = source/row['file']; values = interpret(f, pairs, out/('probe-'+f.name))
        expected = [reference(cases[row['name']], *pair) for pair in pairs]
        mismatches = sum(a != b for a, b in zip(values, expected))
        if row.get('negative'):
            if not mismatches: raise AssertionError('missing negative counterexample')
        elif mismatches: raise AssertionError((row, values, expected))
        rows.append(dict(file=f.name, negative=bool(row.get('negative')), calls=len(pairs),
                         mismatches=mismatches, actual=values, expected=expected))
        target = out/('replay-'+f.name)
        if row['mode'] == 'recovered':
            p.project(source/(row['name']+'-aligned-'+row['opt']+'.wasm'), target)
            identical = target.read_bytes() == (source/(row['name']+'-plain-raw.wasm')).read_bytes()
            if not identical: raise AssertionError('not original bytes')
            identities.append(dict(file=f.name, plain_byte_identical=identical))
        else:
            raw = target if row['opt'] == 'raw' else target.with_name(target.stem+'-before-opt.wasm')
            if row['mode'] == 'plain': p.q.compile(p.plain(cases[row['name']]), raw)
            else: p.transform(source/(row['name']+'-plain-raw.wasm'), raw, row['mode'])
            if row['opt'] == 'O3': p.q.w.tool('wasm-opt', [raw, '-O3', '-o', target])
        identical = target.read_bytes() == f.read_bytes()
        if not identical: raise AssertionError('replay differs')
        replay.append(dict(file=f.name, byte_identical=identical))

    def module(body, extra=''):
        return '(module '+extra+' (func (export "run") (param i32 i32) (result i32) '+body+'))'
    # Erased values must not erase possible traps, calls, memory effects or control.
    negatives = {
        'zero-times-div-zero': module('(i32.wrap_i64 (i64.mul (i64.div_u (i64.const 1) (i64.const 0)) (i64.const 0)))'),
        'zero-times-rem-zero': module('(i32.wrap_i64 (i64.mul (i64.rem_u (i64.const 1) (i64.const 0)) (i64.const 0)))'),
        'dynamic-divisor': module('(i32.wrap_i64 (i64.rem_u (i64.const 7) (i64.extend_i32_u (local.get 0))))'),
        'call-erased': module('(i32.mul (call 0) (i32.const 0))', '(import "h" "f" (func (result i32)))'),
        'memory-effect': module('(i32.store (i32.const 0) (local.get 0)) (local.get 1)', '(memory 1)'),
        'unknown-xor': module('(i32.xor (local.get 0) (local.get 1))'),
        'dynamic-shift': module('(i32.wrap_i64 (i64.shl (i64.const 1) (i64.extend_i32_u (local.get 0))))'),
        'opaque-remainder-output': module('(i32.wrap_i64 (i64.rem_u (i64.extend_i32_u (local.get 0)) (i64.const 65537)))'),
    }
    rejects = []
    for name, text in negatives.items():
        src = out/(name+'.wasm'); p.q.compile(text, src); dst = out/(name+'-recovered.wasm')
        try: p.project(src, dst)
        except ValueError as ex:
            if dst.exists(): raise AssertionError('rejected but emitted')
            rejects.append(dict(name=name, status='unsupported', reason=str(ex)))
        else: raise AssertionError('unsafe acceptance: '+name)
    # Regression: an odd remainder in a zero low-word term still defines a local.
    text = module('(local i64) (i32.wrap_i64 (i64.add (i64.shl (i64.rem_u (local.tee 2 (i64.extend_i32_u (local.get 0))) (i64.const 65537)) (i64.const 32)) (local.get 2)))')
    src = out/'tee-regression.wasm'; dst = out/'tee-regression-recovered.wasm'
    p.q.compile(text, src); p.project(src, dst)
    for f in (src, dst):
        if interpret(f, pairs, out/('probe-'+f.name)) != [a for a, b in pairs]: raise AssertionError('tee ordering')
    syntax = []
    for f in p.HERE.glob('*.py'):
        ast.parse(f.read_text(encoding='utf-8')); syntax.append(f.name)
    result = dict(rows=rows, positive_calls=sum(x['calls'] for x in rows if not x['negative']),
                  negative_calls=sum(x['calls'] for x in rows if x['negative']),
                  positive_mismatches=0, traps=0, replay=replay, identities=identities,
                  rejected=rejects, tee_regression_calls=2*len(pairs), python_syntax=syntax)
    p.q.save(out/'audit.json', result)
    print(json.dumps({k: result[k] for k in ('positive_calls','negative_calls','positive_mismatches','tee_regression_calls')}))


if __name__ == '__main__': main(*sys.argv[1:])
