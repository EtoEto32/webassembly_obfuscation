import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import time
import transform as T


def build(out):
    out.mkdir(parents=True, exist_ok=False)
    rng = random.Random(202610180711)
    entries = []
    for length in (16, 64, 128):
        pattern = bytes(rng.randrange(256) for _ in range(length))
        original = out / f'l{length}-plain-raw.wasm'
        T.assemble(T.source(pattern), original)
        for method in ('plain', 'recompute', 'rolling'):
            raw = out / f'l{length}-{method}-raw.wasm'
            record = {'transformation_ns': 0, 'private_pages': 0}
            if method != 'plain':
                record = T.transform(original, raw, method)
            for opt in ('raw', 'O2', 'O3'):
                path = raw if opt == 'raw' else out / f'l{length}-{method}-{opt}.wasm'
                if opt != 'raw':
                    T.tool('wasm-opt', [raw, '-'+opt, '--enable-multimemory', '--enable-bulk-memory', '-o', path])
                    T.tool('wasm-validate', [path])
                entries.append({'file': path.name, 'length': length, 'method': method, 'opt': opt,
                                'bytes': path.stat().st_size,
                                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **record})
        (out / f'l{length}-truth.json').write_text(json.dumps({'pattern': pattern.hex()}), encoding='utf-8')
    wat, layout = T.group_module(b'A' * 16, 'rolling', audit=True)
    T.assemble(wat, out / 'arithmetic-audit.wasm')
    rejected = []
    for name, wat in [('write', T.source(b'example').replace(T.BOUNDS, T.BOUNDS+'(i32.store (i32.const 0) (i32.const 42))')),
                      ('size', T.source(b'example').replace('1 1)', '2 2)'))]:
        path = out / (name+'.wasm')
        T.assemble(wat, path)
        try:
            T.inspect(path)
        except ValueError as e:
            rejected.append({'name': name, 'status': 'rejected', 'reason': str(e)})
        else:
            raise AssertionError('Unsupported input accepted')
    try:
        T.group_module(bytes(256), 'rolling')
    except ValueError:
        rejected.append({'name': 'length256', 'status': 'rejected'})
    else:
        raise AssertionError('Noninjective input domain accepted')
    manifest = {'entries': entries, 'audit_layout': layout, 'rejected': rejected,
                'prime_hex': hex(T.P), 'q_hex': hex(T.Q), 'generator': T.G,
                'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in Path(__file__).parent.glob('*.py')},
                'versions': {n: T.tool(n, ['--version']).strip()
                             for n in ('wat2wasm', 'wasm-opt', 'wasm-interp')},
                'status': 'Known-principle experimental comparison, not an adopted invention'}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'binaries': len(entries), 'out': str(out)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('output', type=Path)
    build(p.parse_args().output)
