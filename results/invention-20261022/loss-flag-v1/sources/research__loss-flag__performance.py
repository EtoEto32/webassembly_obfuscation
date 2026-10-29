import argparse
import json
import random
import shutil
import statistics
import subprocess
from pathlib import Path
import prototype as p


def run(main, out):
    main, out = Path(main).resolve(), Path(out).resolve()
    manifest = json.loads((main / 'manifest.json').read_text(encoding='utf-8'))
    pins = json.loads((main / 'pins.json').read_text(encoding='utf-8'))
    for name, digest in pins.items():
        if p.q.digest(main / name) != digest:
            raise ValueError('pin mismatch ' + name)
    out.mkdir(parents=True, exist_ok=False)
    work = [(t, repeat) for t in manifest['targets'] if t.get('bench') for repeat in range(3)]
    random.Random(221003).shuffle(work)
    rows = []
    for index, (t, repeat) in enumerate(work):
        result = subprocess.run(['node', '--no-liftoff', '--no-wasm-lazy-compilation',
                                 str(Path(__file__).with_name('bench.cjs')), str(main / t['bench'])],
                                capture_output=True, text=True, timeout=60)
        (out / f'{index:02}.stderr.txt').write_text(result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(result.stderr)
        row = json.loads(result.stdout)
        row.update(file=t['file'], name=t['name'], mode=t['mode'], repeat=repeat, bytes=t['bytes'])
        rows.append(row)
        p.q.save(out / f'{index:02}.json', row)
    summaries = []
    for name in manifest['fixtures']:
        group = {}
        for mode in ('plain', 'eager', 'basis', 'current'):
            subset = [r for r in rows if r['name'] == name and r['mode'] == mode]
            values = [b['ns_per_run'] for r in subset for b in r['batches']]
            process_medians = [statistics.median(b['ns_per_run'] for b in r['batches']) for r in subset]
            group[mode] = dict(median_ns=statistics.median(process_medians),
                               process_medians_ns=process_medians, batch_min_ns=min(values),
                               batch_max_ns=max(values), bytes=subset[0]['bytes'])
        group['name'] = name
        group['current_over_basis'] = group['current']['median_ns'] / group['basis']['median_ns']
        group['current_over_plain'] = group['current']['median_ns'] / group['plain']['median_ns']
        summaries.append(group)
    result = dict(main=str(main), verified_main_pins=len(pins), processes=len(rows),
                  batches=sum(len(r['batches']) for r in rows),
                  short_batches=sum(b['ns'] < 10e6 for r in rows for b in r['batches']),
                  max_rss_kib=[min(r['max_rss_kib'] for r in rows), max(r['max_rss_kib'] for r in rows)],
                  summaries=summaries, rows=rows,
                  limitations='Normal exits only; fixed copy structures; reused evolving state; no CPU affinity/frequency control. RSS is entire Node process, not only Wasm.')
    p.q.save(out / 'runtime.json', result)
    for file in (Path(__file__), Path(__file__).with_name('bench.cjs')):
        shutil.copy2(file, out / ('source-' + file.name))
    p.q.save(out / 'pins.json', {str(f.relative_to(out)): p.q.digest(f) for f in out.rglob('*') if f.is_file()})
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('main')
    ap.add_argument('output')
    args = ap.parse_args()
    run(args.main, args.output)
