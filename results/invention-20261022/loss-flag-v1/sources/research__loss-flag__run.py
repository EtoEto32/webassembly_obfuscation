import argparse
import json
import random
import shutil
import subprocess
import time
import traceback
from pathlib import Path
import prototype as p

FIXTURES = {
    'swap16': (16, [(15, 0, 1), (0, 1, 1), (1, 15, 1)]),
    'cascade32': (32, [(8, 0, 8), (16, 8, 8), (24, 16, 8), (0, 24, 8)]),
    'overlap24': (24, [(1, 0, 12), (6, 3, 12), (0, 8, 8), (16, 0, 8)])}
SEEDS = (221001, 221002)


def snapshot(out):
    sources = out / 'sources'
    sources.mkdir()
    files = [*Path(__file__).parent.glob('*.py'), *Path(__file__).parent.glob('*.cjs'),
             Path(__file__).parent / 'plan.md']
    files += [p.ROOT / f for f in ['research/prefix-repair/prototype.py',
              'research/prefix-repair/recover.py', 'research/copy-centralizer/model.py',
              'research/isotope-swizzle/prototype.py', 'research/connectivity-elimination/prototype.py']]
    for file in files:
        shutil.copy2(file, sources / '__'.join(file.relative_to(p.ROOT).parts))


def run(out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    snapshot(out)
    targets, fixtures, analysis = [], {}, []
    attacker = p.recovery()
    for name, (n, ops) in FIXTURES.items():
        rng = random.Random(20261022 + n)
        data = bytes(rng.randrange(1, 256) for _ in range(n))
        fixtures[name] = dict(n=n, ops=ops, data=list(data))
        source = out / (name + '.source.wasm')
        p.q.compile(p.wat(data, ops), source)
        for seed, mode in [(0, 'plain')] + [(s, mode) for s in SEEDS for mode in ('eager', 'basis', 'current', 'bad')]:
            raw = out / f'{name}.{seed}.{mode}.raw.wasm'
            if mode == 'plain':
                p.q.compile(p.wat(data, ops), raw)
                meta = dict(n=n, ops=ops, matrix=p.m.ident(n), transform_ms=0)
            else:
                meta = p.transform(source, raw, mode, seed)
            opt = out / f'{name}.{seed}.{mode}.O3.wasm'
            p.q.tool('wasm-opt', [raw, '-O3', '--enable-bulk-memory', '-o', opt])
            p.q.w.tool('wasm-validate', [opt])
            for kind, file in [('raw', raw), ('O3', opt)]:
                probe = out / (file.stem + '.probe.wasm')
                p.base.probe(file, probe)
                t = dict(name=name, seed=seed, mode=mode, opt=kind, file=file.name, probe=probe.name,
                         bytes=file.stat().st_size, sha256=p.q.digest(file), meta=meta)
                if kind == 'O3' and mode != 'bad' and seed in (0, SEEDS[0]):
                    bench = out / (file.stem + '.bench.wasm')
                    p.bench(file, bench)
                    t['bench'] = bench.name
                targets.append(t)
                if mode == 'current':
                    recovered = out / (file.stem + '.recovered.wasm')
                    start = time.perf_counter()
                    result = attacker.recover(file, recovered)
                    result.update(file=file.name, recovered=recovered.name,
                                  total_ms=(time.perf_counter() - start) * 1000,
                                  byte_identical_to_source=recovered.read_bytes() == source.read_bytes(), oracle_queries=0)
                    if not result['byte_identical_to_source']:
                        raise AssertionError('unexpected recovered source')
                    analysis.append(result)
                    rp = out / (recovered.stem + '.probe.wasm')
                    p.base.probe(recovered, rp)
                    targets.append(dict(name=name, seed=seed, mode='recovered', opt=kind,
                                        file=recovered.name, probe=rp.name, bytes=recovered.stat().st_size,
                                        sha256=p.q.digest(recovered), meta=dict(n=n, ops=ops, matrix=p.m.ident(n))))
    manifest = dict(targets=targets, fixtures=fixtures, source_note='Three synthetic constant-copy structures, not three applications.')
    p.q.save(out / 'manifest.json', p.safe(manifest))
    p.q.save(out / 'analysis.json', analysis)
    result = subprocess.run(['node', str(Path(__file__).with_name('check.cjs')), str(out)],
                            capture_output=True, text=True, timeout=180)
    (out / 'check-stdout.txt').write_text(result.stdout, encoding='utf-8')
    (out / 'check-stderr.txt').write_text(result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stderr)
    p.q.save(out / 'pins.json', {str(f.relative_to(out)): p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps(dict(output=str(out), targets=len(targets), recoveries=len(analysis), checks=result.stdout)))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('output')
    args = ap.parse_args()
    try:
        run(args.output)
    except Exception:
        dest = Path(args.output)
        if dest.is_dir() and not (dest / 'failure.txt').exists():
            (dest / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise
