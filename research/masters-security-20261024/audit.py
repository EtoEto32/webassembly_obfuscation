"""Finite independent checks for the October 24 feasibility probes."""
import argparse
import ast
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('probe', HERE / 'probe.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def main(source, out):
    out.mkdir(parents=True, exist_ok=False)
    pins = json.loads((source / 'sha256.json').read_text())
    for name, expected in pins.items():
        assert hashlib.sha256((source / name).read_bytes()).hexdigest() == expected, name
    manifest = json.loads((source / 'manifest.json').read_text())
    recomputed = []
    for entry in manifest:
        binary = source / entry['file']
        assert p.digest(binary) == entry['sha256']
        p.w.tool('wasm-validate', [binary])
        if 'summary' in entry:
            actual = p.summarize(p.w.parse(p.w.tool('wasm2wat', [binary, '--fold-exprs'])))
            assert actual == entry['summary']
            recomputed.append(entry['file'])
    # Independent combinatorial model: the masking construction preserves the
    # whole requested pre-call view for every actual mutation subset of W.
    bits = 6
    checked = 0
    for read in range(1 << bits):
        for maywrite in range(1 << bits):
            keep = read & maywrite
            actual = maywrite
            while True:
                for before in (0, 0b010101, 0b101010, 0b111111):
                    after = before ^ actual
                    reconstructed = (before & keep) | (after & read & ~keep)
                    assert reconstructed == before & read
                    checked += 1
                if actual == 0:
                    break
                actual = (actual-1) & maywrite
    # Minimized counterexample if a real write is omitted from the summary.
    negative = {'read': 1, 'declared_write': 0, 'actual_write': 1,
                'before': 0, 'after': 1, 'reconstructed': 1}
    assert negative['reconstructed'] != negative['before']

    def normalized(wat, name, flags=()):
        q = out / (name + '.wat')
        q.write_text(wat, encoding='utf8')
        b = q.with_suffix('.wasm')
        p.w.tool('wat2wasm', [q, '-o', b, *flags])
        p.w.tool('wasm-validate', [b, *flags])
        return p.w.parse(p.w.tool('wasm2wat', [b, '--fold-exprs', *flags]))
    shared = normalized('(module (memory 1 1 shared) (func (export "callback") (param i32 i32 i32) nop))', 'reject-shared', ['--enable-threads'])
    assert p.summarize(shared)['kind'] == 'reject'
    unknown = normalized('(module (import "x" "y" (func $y)) (memory 1) (func (export "callback") (param i32 i32 i32) call $y))', 'fallback-import')
    assert p.summarize(unknown)['kind'] == 'full'
    growing = normalized('(module (memory 1 2) (func (export "callback") (param i32 i32 i32) (drop (memory.grow (i32.const 1)))))', 'fallback-grow')
    assert p.summarize(growing)['kind'] == 'full'

    # WABT independent interpreter: a scalar write survives a later trap.
    wat = '(module (memory 1) (func (export "write_then_trap") (i32.store (i32.const 0) (i32.const 7)) unreachable) (func (export "read_after") (result i32) (i32.load (i32.const 0))))'
    normalized(wat, 'trap-persists')
    log = p.w.tool('wasm-interp', [out / 'trap-persists.wasm', '--run-all-exports'])
    assert 'error: unreachable executed' in log and 'i32:7' in log, log
    (out / 'wabt-trap.txt').write_text(log, encoding='utf8')
    for f in HERE.glob('*.py'):
        ast.parse(f.read_text(encoding='utf8'))
    subprocess.run(['node', '--check', str(HERE / 'probe.cjs')], check=True, capture_output=True)
    unrelated = {}
    for name, expected in {
        'paper/main.tex': 'db94c578a9d573b700756daeebaabfbcbfc3fa0c896ac1a47d491bc09cc12225',
        'paper/README.md': '10e8eee3c2f27f66a7f2df2d4807f4aca97bde8a49eb8f2a3be186e6d550f2d0'
    }.items():
        unrelated[name] = p.digest(p.ROOT / name)
        assert unrelated[name] == expected
    report = {'pinsVerified': len(pins), 'wasmValidated': len(manifest), 'summariesRecomputed': len(recomputed),
              'finiteSnapshotChecks': checked, 'finiteDomainBits': bits, 'negativeControl': negative,
              'sharedRejected': True, 'importFallback': True, 'growFallback': True,
              'wabtTrapPersistence': True, 'unrelatedHashes': unrelated}
    shutil.copy2(__file__, out / 'audit.py')
    (out / 'audit.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    (out / 'sha256.json').write_text(json.dumps({q.name:p.digest(q) for q in out.iterdir() if q.is_file()}, indent=2), encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    a = parser.parse_args()
    main(a.source.resolve(), a.output.resolve())
