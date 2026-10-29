"""Read-only audit of saved experiments; writes one separately named receipt."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics
import prototype as p
import attack as a

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'results/invention-20261019'

def read(folder, name):
    return json.loads((BASE / folder / name).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('output', type=Path)
    opt = ap.parse_args()
    if opt.output.exists():
        raise FileExistsError(opt.output)
    checks = {}
    audited_hashes = {}
    total_calls = total_binaries = canonical = 0
    canonical_nonconstant = canonical_constant = 0
    for folder, expected in [('hurwitz-support-v3', 100), ('hurwitz-support-edge-v1', 36)]:
        manifest = read(folder, 'manifest.json')
        correct = read(folder, 'correctness.json')
        files = manifest['files']
        assert len(files) == expected == correct['binaries']
        assert correct['mismatches'] == correct['traps'] == 0
        assert correct['calls'] == sum(x['inputs'] for x in correct['rows'])
        assert {x['path'] for x in files} == {x['path'] for x in correct['rows']}
        for row in files:
            path = BASE / folder / row['path']
            assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes']
            audited_hashes[str(path.relative_to(ROOT))] = row['sha256']
            if '.' in row['mode']:
                bb = a.BDD()
                root = bb.source(manifest['models'][row['model']])
                assert path.with_suffix('.wat').read_text(encoding='utf-8') == bb.wasm(root)
                canonical += 1
                if root > 0:
                    canonical_nonconstant += 1
                else:
                    canonical_constant += 1
        total_calls += correct['calls']
        total_binaries += len(files)
    assert (total_calls, total_binaries, canonical, canonical_nonconstant, canonical_constant) == (2943776, 136, 66, 56, 10)
    checks['native_and_canonical'] = dict(calls=total_calls, binaries=total_binaries,
        canonical=canonical, nonconstant=canonical_nonconstant, constant=canonical_constant)
    statuses = Counter(q['status'] for q in read('hurwitz-support-v3', 'attacks.json') + read('hurwitz-support-edge-v1', 'analysis.json'))
    assert statuses == {'recovered': 66}
    checks['attack_statuses'] = dict(statuses)
    previous = {q['path']: q['sha256'] for q in read('hurwitz-support-v2', 'manifest.json')['files']}
    current = read('hurwitz-support-v3', 'manifest.json')['files']
    assert all(previous[q['path']] == q['sha256'] == sha(BASE / 'hurwitz-support-v2' / q['path']) for q in current)
    replay = read('hurwitz-support-v3', 'replay.json')
    assert len(replay['same']) == 100 and replay['different'] == []
    checks['byte_replay'] = 100
    env = read('hurwitz-support-v3', 'environment.json')
    core = [HERE / x for x in ['prototype.py', 'attack.py', 'run.py', 'check.cjs']]
    core += [ROOT / 'research' / x / 'prototype.py' for x in ['lane-demand', 'output-recurrence', 'connectivity-elimination']]
    for path in core:
        name = path.parent.name + '_' + path.name
        assert sha(path) == env['sources'][name] == sha(BASE / 'hurwitz-support-v3/sources' / name)
    for name in ['measure.py', 'batch.cjs']:
        assert sha(HERE / name) == sha(BASE / 'hurwitz-support-batch-v1/sources' / name)
    checks['contemporaneous_sources_unchanged'] = 9
    verification = read('hurwitz-support-verify-v1', 'verification.json')
    assert verification['status'] == 'completed'
    assert verification['constant_pair_move_checks'] == 28800
    assert verification['input_dependent_move_checks'] == 8192
    assert len(verification['canonical_equal']) == 50
    assert verification['interpreter_calls'] == 600
    assert len(verification['refusals']) == 4
    assert verification['wrong_swap_witness']['actual'] != verification['wrong_swap_witness']['expected']
    checks['verification'] = dict(interpreter_calls=600, move_checks=36992, refusals=4, bad_swap=True)
    benchmark = read('hurwitz-support-batch-v1', 'benchmark.json')
    perf = read('hurwitz-support-batch-v1', 'summary.json')
    harness = read('hurwitz-support-batch-v1', 'correctness.json')
    assert len(benchmark) == 90 and len(perf) == 30
    assert harness == dict(harnesses=30, tests=600, referenceCalls=6120, mismatches=0)
    for q in perf:
        records = [b for b in benchmark if b['path'] == q['path']]
        assert len(records) == 3 and {b['repeat'] for b in records} == {0, 1, 2}
        assert statistics.median(b['median_ns'] for b in records) == q['median_ns']
        assert sha(BASE / 'hurwitz-support-batch-v1' / q['path']) == q['harness_sha256']
        for b in records:
            assert b['warmup_calls'] == 100000 and b['calls_per_sample'] == 10000
            assert b['repetitions'] == len(b['samples_ns']) == 11
    checks['benchmark'] = dict(harnesses=30, fresh_processes=90, tests=600)
    simd = {}
    for model in read('hurwitz-support-v3', 'manifest.json')['models']:
        text = p.w.tool('wasm2wat', [BASE / 'hurwitz-support-v3' / (model + '.braid.O3.wasm')])
        swizzle = text.count('i8x16.swizzle')
        loads = text.count('v128.load')
        assert swizzle > 0 and loads > 0
        simd[model] = dict(swizzles=swizzle, loads=loads)
    checks['O3_persistence'] = simd
    broken = []
    for path in HERE.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' not in link and not link.startswith('#'):
                if not (path.parent / link.split('#')[0]).exists():
                    broken.append([path.name, link])
    assert not broken, broken
    checks['documentation_links'] = 'passed'
    # These are audit-time hashes, not a claim that these files were snapshotted before execution.
    for path in HERE.iterdir():
        if path.is_file():
            audited_hashes[str(path.relative_to(ROOT))] = sha(path)
    for folder in ['hurwitz-support-v3', 'hurwitz-support-edge-v1', 'hurwitz-support-verify-v1', 'hurwitz-support-batch-v1']:
        for path in (BASE / folder).glob('*.json'):
            audited_hashes[str(path.relative_to(ROOT))] = sha(path)
    result = dict(status='passed', audited_at_utc=datetime.now(timezone.utc).isoformat(),
        checks=checks, audit_time_sha256=audited_hashes, goal_complete=False,
        scope='Saved-result consistency and current sources; no new performance samples. v1 is an implementation failure, excluded from effect counts.')
    opt.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(dict(status='passed', checks=checks, hash_count=len(audited_hashes), goal_complete=False)))

if __name__ == '__main__':
    main()
