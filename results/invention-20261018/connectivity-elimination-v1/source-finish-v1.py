"""Complete the recovery revision, corruption control, interpreter and timings.

Existing build/first-recovery evidence is retained. Writes only new artifacts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import struct
import subprocess
import prototype as p
import recover


def write_new(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2)
        f.write('\n')


def revise(directory):
    build = json.loads((directory / 'build.json').read_text())
    results = []
    for row in build['conditions']:
        src = directory / row['file']
        out = directory / 'recovered-v2' / row['file']
        try:
            result = recover.recover(src, out)
        except OverflowError as exc:
            result = {'status': 'budget_exhausted', 'message': str(exc)}
        except Exception as exc:
            result = {'status': 'error', 'message': repr(exc)}
        results.append({'file': row['file'], **result})
    write_new(directory / 'recovery-v2.json', {'reason': 'Model zero-initialized memory beyond active data; v1 incorrectly treated optimized zero tails as truncation.', 'results': results})
    (directory / 'source-recover-v2.py').write_bytes(Path(recover.__file__).read_bytes())
    binary = bytearray((directory / 'mixed12-graph-raw.wasm').read_bytes())
    marker = struct.pack('<I', p.MAGIC)
    start = binary.find(marker)
    assert start >= 0 and binary.find(marker, start + 1) < 0
    h = struct.unpack_from('<13I', binary, start)
    count = 0
    for i in range(h[3]):
        pos = start + h[8] + 12*i
        op, _, _ = struct.unpack_from('<3I', binary, pos)
        if op == 0:
            struct.pack_into('<3I', binary, pos, 1, 0, 0)
            count += 1
    with (directory / 'mutation-control.wasm').open('xb') as f:
        f.write(binary)
    p.tool('wasm-validate', [directory / 'mutation-control.wasm'])
    write_new(directory / 'mutation-control.json', {'changed_input_labels_to_zero': count,
        'description': 'An intentionally incorrect but valid graph program, used to test output mismatch detection.',
        'sha256': hashlib.sha256(binary).hexdigest()})
    print(json.dumps({'recovery': {s: sum(r['status'] == s for r in results) for s in set(r['status'] for r in results)}}), flush=True)


def interpreter(directory):
    build = json.loads((directory / 'build.json').read_text())
    fixtures = json.loads((directory / 'fixtures.json').read_text())
    inputs = json.loads((directory / 'inputs.json').read_text())
    dest = directory / 'interpreter'
    dest.mkdir(exist_ok=False)
    def evaluate(t, x):
        if t[0] == 'var': return x[t[1]]
        if t[0] == 'const': return t[1]
        a, b = evaluate(t[1], x), evaluate(t[2], x)
        return {'and': a & b, 'or': a | b, 'xor': a ^ b}[t[0]] & p.MASK
    results = []
    for row in build['conditions']:
        src = directory / row['file']
        cases = [inputs[row['kernel']][i] for i in (0, 4, -1, -2)]
        wat = p.tool('wasm2wat', [src])
        calls = []
        for j, xs in enumerate(cases):
            args = ' '.join(f'(i32.const {v if v < 2**31 else v-2**32})' for v in xs)
            calls.append(f'(func (export "case{j}") (result i32) (call 0 {args}))')
        wp = dest / (src.stem + '.wat')
        wp.write_text(wat.rstrip()[:-1] + '\n' + '\n'.join(calls) + ')', encoding='utf-8')
        binary = wp.with_suffix('.wasm')
        p.tool('wat2wasm', [wp, '-o', binary])
        log = p.tool('wasm-interp', [binary, '--run-all-exports'])
        expected = [evaluate(fixtures[row['kernel']]['tree'], xs) for xs in cases]
        for j, value in enumerate(expected):
            if f'case{j}() => i32:{value}' not in log:
                raise AssertionError({'file': str(binary), 'log': log, 'expected': expected})
        results.append({'file': src.name, 'expected': expected, 'output': log, 'status': 'passed'})
    write_new(directory / 'interpreter.json', {'calls': 4*len(results), 'mismatches': 0, 'results': results})
    print(json.dumps({'interpreter_calls': 4*len(results), 'mismatches': 0}), flush=True)


def timing(directory):
    build = json.loads((directory / 'build.json').read_text())
    rows = list(build['conditions'])
    random.Random(0x42434445).shuffle(rows)
    worker = Path(__file__).with_name('verify.cjs')
    results = []
    dest = directory / 'timing'
    dest.mkdir(exist_ok=False)
    for row in rows:
        run = subprocess.run(['node', str(worker), '--timing', str(directory / row['file']), str(row['n'])],
                             capture_output=True, text=True, timeout=30)
        if run.returncode:
            raise RuntimeError(run.stderr)
        result = json.loads(run.stdout)
        result['median_ns'] = statistics.median(result['samples_ns'])
        ordered = sorted(result['samples_ns'])
        result['q1_ns'], result['q3_ns'] = ordered[2], ordered[6]
        result.update({k: row[k] for k in ('kernel', 'mode', 'opt', 'bytes')})
        write_new(dest / (row['file'] + '.json'), result)
        results.append(result)
    write_new(directory / 'timing.json', {'results': results, 'fresh_processes': len(results),
        'order_seed': '0x42434445', 'note': 'One fresh process per binary, nine warmed in-process trials. No process-level replication, CPU pinning or confidence interval.'})
    print(json.dumps({'timed_conditions': len(results)}), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['revise', 'interpreter', 'timing'])
    ap.add_argument('directory', type=Path)
    a = ap.parse_args()
    globals()[a.stage](a.directory)
