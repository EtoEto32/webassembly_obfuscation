"""Replay binaries, validate snapshot inputs and measure fresh-process update costs."""
import argparse
import collections
import json
import random
import shutil
import statistics
import subprocess
import sys
from pathlib import Path
import prototype as p
from attack import recover

parser = argparse.ArgumentParser()
parser.add_argument('main')
parser.add_argument('out')
args = parser.parse_args()
main, out = Path(args.main).resolve(), Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=False)
def save(name, x):
    (out/name).write_text(json.dumps(x, indent=2, ensure_ascii=False), encoding='utf-8')
tasks = json.loads((main/'tasks.json').read_text())
pins = json.loads((main/'hashes.json').read_text())
for file, digest in pins.items():
    assert p.q.digest(main/file) == digest, file
for file, digest in json.loads((main/'dependencies.json').read_text()).items():
    assert p.q.digest(p.ROOT/file) == digest, file
replay = []
for task in tasks:
    if task['stage'] != 'raw' or task['audit']:
        continue
    raw = out/Path(task['file']).name
    p.q.compile((p.array_text if task['mode'] == 'array' else p.poly_text)(task['items']), raw)
    for stage in ('raw', 'O3'):
        f = raw if stage == 'raw' else raw.with_name(raw.name.replace('-raw.', '-O3.'))
        if stage == 'O3':
            p.q.tool('wasm-opt', [raw, '-O3', '--enable-bulk-memory', '-o', f])
        audit = f.with_name(f.stem+'-audit.wasm')
        p.instrument(f, audit)
        for candidate in (f, audit):
            assert candidate.read_bytes() == (main/candidate.name).read_bytes(), candidate
            replay.append(dict(file=candidate.name, byte_identical=True))
save('replay.json', replay)
sample = next(x for x in json.loads((main/'snapshot-oracle.json').read_text())
              if x['expected'] == 'recovered' and x['id'].startswith('n32-poly-O3'))
before, after = (main/sample['before']).read_bytes(), (main/sample['after']).read_bytes()
invalid = []
for label, b in [('truncated', before[:-1]), ('bad_n', b'\xff\xff\xff\xff'+before[4:])]:
    try:
        recover(b, after)
    except ValueError as e:
        invalid.append(dict(case=label, rejected=True, reason=str(e)))
    else:
        raise AssertionError(label)
save('invalid-inputs.json', invalid)
jobs = [(task, repeat) for task in tasks
        if task['stage'] == 'O3' and not task['audit'] and task['id'].split('-')[0] in ('n8', 'n32')
        for repeat in range(3)]
random.Random(21102178).shuffle(jobs)
rows = []
for task, repeat in jobs:
    file = out/f"{task['id']}-{repeat}.json"
    save(file.name, dict(id=task['id'], file=task['file'], items=task['items']))
    command = ['node', '--no-liftoff', '--no-wasm-lazy-compilation',
               str(Path(__file__).with_name('bench.cjs')), str(file)]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (out/f'{file.stem}-stdout.txt').write_text(proc.stdout, encoding='utf-8')
    (out/f'{file.stem}-stderr.txt').write_text(proc.stderr, encoding='utf-8')
    proc.check_returncode()
    rows.append(dict(**json.loads(proc.stdout), repeat=repeat, command=command))
    print(json.dumps(dict(measured=file.stem)), flush=True)
save('runtime.json', rows)
groups = {}
for row in rows:
    groups.setdefault(row['id'], []).append(row)
summary = []
for name, rs in sorted(groups.items()):
    xs = [r['medianNs'] for r in rs]
    summary.append(dict(id=name, process_medians_ns=xs, median_ns=statistics.median(xs),
                        peak_rss_kib=[min(r['peakRssKiB'] for r in rs), max(r['peakRssKiB'] for r in rs)],
                        min_batch_ms=min(min(r['batchMs']) for r in rs)))
save('summary.json', dict(verified_pins=len(pins), replay=len(replay), malformed_rejections=invalid,
                          runtime=summary, note='3 fresh processes x 9 batches; CPU affinity/frequency not fixed'))
source = out/'sources'
source.mkdir()
for f in Path(__file__).parent.iterdir():
    if f.suffix in ('.py', '.cjs', '.md'):
        shutil.copy2(f, source/f.name)
save('hashes.json', {str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()})
print((out/'summary.json').read_text(), flush=True)
