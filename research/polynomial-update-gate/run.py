"""Build real mutable Wasm fixtures and audit snapshot-only adaptive recovery."""
import argparse
import collections
import json
import platform
import random
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path
import prototype as p
from attack import recover


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('out')
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    snap = out/'sources'
    snap.mkdir()
    for f in Path(__file__).parent.iterdir():
        if f.suffix in ('.py', '.cjs', '.md'):
            shutil.copy2(f, snap/f.name)
    def save(name, data):
        (out/name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    rng = random.Random(21102177)
    fixtures = {
        'empty': [], 'single': [(17, 0)], 'two': [(1, 0), (p.P-1, 0xffffffff)],
        'boundary': [(0, 0), (1, 1), (0x80000000, p.P), (p.P-1, 0xffffffff)]
                    + [(p.P+i, i) for i in range(5)],
        'duplicate': [(8, 42), (8, 7), (0, 0), (p.P, 0xffffffff)],
        'n8': [(k, rng.randrange(2**32)) for k in rng.sample(range(p.P), 8)],
        'n32': [(k, rng.randrange(2**32)) for k in rng.sample(range(p.P), 32)],
    }
    tasks, builds = [], []
    bounds = [0, 1, p.P-1, p.P, p.P+1, p.P+4, 0x80000000, 0xffffffff]
    for name, raw_items in fixtures.items():
        items = p.canonical(raw_items)
        ops = [[k, v] for k, v in items]  # No-op controls.
        for k, _ in items[:2]:
            # The 0 -> p update changes the upper quotient alone.
            ops.extend([[k, v] for v in bounds])
            ops.extend([[k, 0], [k, p.P], [k, 0]])
        ops.extend([[k, rng.randrange(2**32)] for k in bounds])
        keys = [k for k, _ in items]
        for i in range(128):
            key = rng.choice(keys) if keys and i % 3 else rng.randrange(2**32)
            ops.append([key, rng.randrange(2**32)])
        for mode in ('array', 'poly'):
            t0 = time.perf_counter_ns()
            text = (p.array_text if mode == 'array' else p.poly_text)(raw_items)
            t1 = time.perf_counter_ns()
            raw = out/f'{name}-{mode}-raw.wasm'
            p.q.compile(text, raw)
            t2 = time.perf_counter_ns()
            for stage in ('raw', 'O3'):
                file = raw if stage == 'raw' else out/f'{name}-{mode}-{stage}.wasm'
                if stage == 'O3':
                    p.q.tool('wasm-opt', [raw, '-O3', '--enable-bulk-memory', '-o', file])
                    p.q.w.tool('wasm-validate', [file])
                instrumented = file.with_name(file.stem+'-audit.wasm')
                p.instrument(file, instrumented)
                for audit, f in ((False, file), (True, instrumented)):
                    tasks.append(dict(id=f.stem, file=str(f), mode=mode, stage=stage, audit=audit,
                                      items=items, ops=ops))
                builds.append(dict(name=name, mode=mode, stage=stage, file=str(file),
                    bytes=file.stat().st_size, linear_memory_bytes=65536,
                    generate_ms=(t1-t0)/1e6, compile_validate_ms=(t2-t1)/1e6,
                    note='generation timing is shared by raw/O3; not arbitrary-Wasm transformation'))
        print(json.dumps(dict(built=name)), flush=True)
    save('tasks.json', tasks)
    save('builds.json', builds)
    proc = subprocess.run(['node', str(Path(__file__).with_name('check.cjs')), str(out/'tasks.json'), str(out)],
                          capture_output=True, text=True, timeout=90)
    (out/'check-stdout.txt').write_text(proc.stdout, encoding='utf-8')
    (out/'check-stderr.txt').write_text(proc.stderr, encoding='utf-8')
    proc.check_returncode()
    checks = json.loads(proc.stdout)
    save('checks.json', checks)
    rows = []
    for item in json.loads((out/'snapshot-oracle.json').read_text()):
        before, after = (out/item['before']).read_bytes(), (out/item['after']).read_bytes()
        # The recovery function receives bytes only; the oracle is used for scoring afterwards.
        times = []
        for _ in range(11):
            t0 = time.perf_counter_ns()
            result = recover(before, after)
            times.append((time.perf_counter_ns()-t0)/1000)
        assert result['status'] == item['expected'], (item, result)
        if 'key' in item:
            assert all(result[x] == item[x] for x in ('key', 'old', 'new')), (item, result)
        rows.append(dict(id=item['id'], **result, analysis_us=statistics.median(times), samples_us=times))
    save('recovery.json', rows)
    # A separate process sees only two snapshot paths, not task metadata or the update arguments.
    sample = next(x for x in json.loads((out/'snapshot-oracle.json').read_text())
                  if x['id'].startswith('n32-poly-O3') and x['expected'] == 'recovered')
    proc = subprocess.run([sys.executable, str(Path(__file__).with_name('attack.py')),
                           str(out/sample['before']), str(out/sample['after'])], capture_output=True, text=True, timeout=30)
    proc.check_returncode()
    result = json.loads(proc.stdout)
    assert result['key'] == sample['key']
    save('isolated-attack.json', dict(sample=sample['id'], result=result, stderr=proc.stderr))
    save('summary.json', dict(binaries=len(tasks), calls=checks['calls'], mismatches=0,
         snapshots=len(rows), statuses=dict(collections.Counter(x['status'] for x in rows)),
         upper_only=sum(x.get('active_components') == [1] for x in rows),
         analysis_us_range=[min(x['analysis_us'] for x in rows), max(x['analysis_us'] for x in rows)],
         environment=dict(python=sys.version, platform=platform.platform(), node=checks['node'], v8=checks['v8']),
         claim='known-interpolation extension is rejected; not a new obfuscation invention'))
    # Pin all local data and the exact imported shared implementation.
    pins = {str(f.relative_to(out)): p.q.digest(f) for f in out.rglob('*') if f.is_file()}
    save('hashes.json', pins)
    dependencies = [p.ROOT/'research/polynomial-lookup'/f for f in ('field.py','prototype.py')]
    dependencies += [p.ROOT/'research/isotope-swizzle/prototype.py', p.ROOT/'research/connectivity-elimination/prototype.py']
    save('dependencies.json', {str(f.relative_to(p.ROOT)): p.q.digest(f) for f in dependencies})
    print((out/'summary.json').read_text(), flush=True)


if __name__ == '__main__':
    main()
