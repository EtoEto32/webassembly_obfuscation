"""Known-representation controls, not a proposed new obfuscation algorithm."""
import argparse
import json
from pathlib import Path
import random
import shutil
import struct
import subprocess
import time
import instrument as I


def fixture(n, seed, cycle, mode):
    rng = random.Random(seed)
    order = list(range(n))
    rng.shuffle(order)
    addresses = [256 + 16 * i for i in range(n)]
    values = [rng.getrandbits(32) if i % 3 else rng.choice(addresses) for i in range(n)]
    nxt = [0] * n
    for a, b in zip(order, order[1:]):
        nxt[a] = addresses[b]
    if cycle:
        nxt[order[-1]] = addresses[order[0]]
    data = bytearray(16 * n)
    for i, p in enumerate(addresses):
        lane = ((p >> 4) & 1) if mode != 'fixed' else 0
        encoded = nxt[i] ^ ((p * 0x9e3779b1) & 0xffffffff) if mode == 'encoded' else nxt[i]
        struct.pack_into('<I', data, 16 * i + 4 * lane, encoded)
        struct.pack_into('<I', data, 16 * i + 4 * (1 - lane), values[i])
    off = '(i32.shl (i32.and (i32.shr_u (local.get $p) (i32.const 4)) (i32.const 1)) (i32.const 2))'
    nextaddr = '(local.get $p)' if mode == 'fixed' else f'(i32.add (local.get $p) {off})'
    valueaddr = '(i32.add (local.get $p) (i32.const 4))' if mode == 'fixed' else f'(i32.add (local.get $p) (i32.xor {off} (i32.const 4)))'
    nextval = f'(i32.load {nextaddr})'
    if mode == 'encoded':
        nextval = f'(i32.xor {nextval} (i32.mul (local.get $p) (i32.const -1640531535)))'
    encoded_data = ''.join('\\%02x' % x for x in data)
    wat = f'''(module
      (memory 1)
      (data (i32.const 256) "{encoded_data}")
      (func (export "run") (param $start i32) (param $limit i32) (result i32)
        (local $p i32) (local $left i32) (local $acc i32)
        (if (i32.ge_u (local.get $start) (i32.const {n})) (then unreachable))
        (local.set $p (i32.add (i32.const 256) (i32.shl (local.get $start) (i32.const 4))))
        (local.set $left (i32.and (local.get $limit) (i32.const 255)))
        (block $done (loop $loop
          (br_if $done (i32.eqz (local.get $left)))
          (br_if $done (i32.eqz (local.get $p)))
          (local.set $acc (i32.xor (i32.rotl (local.get $acc) (i32.const 5)) (i32.load {valueaddr})))
          (local.set $p {nextval})
          (local.set $left (i32.sub (local.get $left) (i32.const 1)))
          (br $loop)))
        (local.get $acc)))'''
    return wat, {'nodes': n, 'seed': seed, 'cycle': cycle, 'head_index': order[0],
                 'values': values, 'next': nxt, 'addresses': addresses}


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    (out / 'source').mkdir()
    for p in Path(__file__).parent.glob('*'):
        if p.is_file() and p.suffix in ('.py', '.cjs', '.md'):
            shutil.copyfile(p, out / 'source' / p.name)
    opt = I.TOOLS / 'binaryen-version_133/bin/wasm-opt.exe'
    rows, truth = [], {}
    for family, n, seed, cycle in [('chain48', 48, 20261018, False),
                                  ('cycle96', 96, 20261019, True),
                                  ('chain128', 128, 20261020, False)]:
        for mode in ('fixed', 'per-node', 'encoded'):
            wat, tr = fixture(n, seed, cycle, mode)
            truth[family] = tr
            wp = out / (family + '-' + mode + '.wat')
            wp.write_text(wat, encoding='utf-8')
            raw = wp.with_suffix('.wasm')
            I.tool('wat2wasm', [wp, '-o', raw])
            for level in ('raw', 'O2', 'O3'):
                p = raw if level == 'raw' else out / (raw.stem + '-' + level + '.wasm')
                if level != 'raw':
                    subprocess.run([str(opt), str(raw), '-' + level, '-o', str(p)],
                                   check=True, capture_output=True, timeout=30)
                I.tool('wasm-validate', [p])
                traced = out / (p.stem + '-traced.wasm')
                t0 = time.perf_counter()
                report = I.transform(p, traced)
                rows.append({'family': family, 'mode': mode, 'optimization': level,
                             'wasm': p.name, 'traced': traced.name, 'bytes': p.stat().st_size,
                             'traced_bytes': traced.stat().st_size, 'sha256': I.sha(p),
                             'traced_sha256': I.sha(traced), 'sites': report['sites'],
                             'instrument_seconds': time.perf_counter() - t0})
    manifest = {'purpose': 'Evaluate memory graph recovery on known controls; no new obfuscator claim',
                'wabt': I.tool('wasm-validate', ['--version']).strip(),
                'binaryen': subprocess.run([str(opt), '--version'], check=True, capture_output=True, text=True).stdout.strip(),
                'source_sha256': {p.name: I.sha(p) for p in (out / 'source').iterdir()},
                'rows': rows, 'truth': truth, 'memory_bytes': 65536}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'binaries': len(rows) * 2, 'conditions': len(rows), 'out': str(out)}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('output', type=Path)
    main(ap.parse_args().output)
