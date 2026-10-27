"""Audit saved evidence; do not rerun timed performance measurements."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
import prototype as p

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'results/invention-20261019'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(folder, name):
    return json.loads((BASE / folder / name).read_text(encoding='utf-8'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('output', type=Path)
    a = ap.parse_args()
    checks = {}
    current, previous = 'lane-demand-v3', 'lane-demand-v2'
    summary = read(current, 'summary.json')
    manifest = read(current, 'manifest.json')
    assert len(summary) == len(manifest['files']) == 56
    assert len({r['path'] for r in summary}) == 56
    assert {r['path'] for r in summary} == {r['path'] for r in manifest['files']}
    for row in summary:
        path = BASE / current / row['path']
        assert path.stat().st_size == row['bytes']
        assert digest(path) == row['sha256']
        assert path.read_bytes() == (BASE / previous / row['path']).read_bytes()
    replay = read(current, 'replay.json')
    assert len(replay) == 56 and all(replay.values())
    checks['binary_hashes_and_byte_replay'] = 56
    hashes = read(current, 'environment.json')['source_sha256']
    for path, expected in hashes.items():
        source = ROOT / path
        snapshot = BASE / current / 'sources' / (source.parent.name + '_' + source.name)
        assert digest(source) == digest(snapshot) == expected, path
    checks['execution_source_hashes_match'] = len(hashes)
    correct = read(current, 'correctness.json')
    extra = read('lane-demand-verify-v2/random', 'correctness.json')
    for value, binaries, calls in [(correct, 56, 240128), (extra, 60, 257280)]:
        assert (value['binaries'], value['calls'], value['mismatches'], value['traps']) == (binaries, calls, 0, 0)
        assert (value['boundary'], value['walking_bit'], value['random']) == (64, 128, 4096)
        assert len(value['records']) == binaries
        assert sum(r['calls'] for r in value['records']) == calls
    checks['native_correctness_binaries'] = 116
    checks['native_correctness_calls'] = correct['calls'] + extra['calls']
    interp = read('lane-demand-verify-v2', 'interpreter.json')
    assert (interp['calls'], interp['mismatches']) == (336, 0)
    assert len(interp['records']) == 56
    assert sum(r['calls'] for r in interp['records']) == 336
    checks['interpreter_calls'] = interp['calls']
    controls = read('lane-demand-verify-v2', 'controls.json')
    assert sum(r['status'] == 'refused' for r in controls) == 4
    cursor = next(r for r in controls if r['name'] == 'nonzero_cursor')
    assert (cursor['status'], cursor['calls'], cursor['zero_cursor_would_be_wrong']) == ('matched', 64, 24)
    assert len(cursor['witnesses']) == 32
    assert all(w['actual'] == [w['expected'], w['expected']] for w in cursor['witnesses'])
    checks['refusal_controls'] = 4
    checks['nonzero_cursor_calls'] = 64
    attacks = read(current, 'attacks.json')
    assert len(attacks) == 24 and all(r['status'] == 'recovered' for r in attacks)
    for row in attacks:
        assert len(row['samples_ms']) == 7
        assert row['median_scalarize_ms'] == statistics.median(row['samples_ms'])
    checks['recovered_scalar_binaries'] = 24
    bench = read(current, 'benchmark.json')
    assert len(bench) == 168
    for row in summary:
        group = [b for b in bench if b['path'] == row['path']]
        assert len(group) == 3 and {b['repeat'] for b in group} == {0, 1, 2}
        assert row['median_ns'] == statistics.median(b['median_ns'] for b in group)
        assert row['range_ns'] == [min(b['median_ns'] for b in group), max(b['median_ns'] for b in group)]
        for b in group:
            assert (b['warmup'], b['repetitions'], b['calls_per_sample']) == (10000, 11, 10000)
            assert len(b['samples_ns']) == 11
            assert b['median_ns'] == statistics.median(b['samples_ns'])
    checks['fresh_benchmark_processes'] = len(bench)
    proof = read('lane-demand-proof-v1', 'proof.json')
    assert (proof['unsat'], proof['sat'], proof['unknown']) == (24, 0, 0)
    assert len(proof['records']) == 24 and all(r['result'] == 'unsat' for r in proof['records'])
    assert (proof['cursor_identity'], proof['negative_cursor_status']) == ('unsat', 'sat')
    queries = list((BASE / 'lane-demand-proof-v1').rglob('*.smt2'))
    assert len(queries) == 24
    checks['scalar_equivalence_unsat_queries'] = len(queries)
    swizzles = {}
    for model in manifest['models']:
        path = BASE / current / (model + '.dynamic.O3.wasm')
        wat = p.w.tool('wasm2wat', [path])
        count = wat.count('i8x16.swizzle')
        assert count > 0
        swizzles[model] = count
    checks['dynamic_O3_remaining_swizzles'] = swizzles
    local_links = 0
    for path in HERE.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if link.startswith(('http:', 'https:', '#')):
                continue
            target = (path.parent / link.split('#', 1)[0]).resolve()
            assert target.exists() or target == a.output.resolve(), (path, target)
            local_links += 1
    checks['existing_local_document_links'] = local_links
    folders = ['lane-demand-probe-v1', 'lane-demand-v1', previous, current,
               'lane-demand-verify-v1', 'lane-demand-verify-v2', 'lane-demand-proof-v1']
    artifacts = {str(path.relative_to(ROOT)): digest(path)
                 for folder in folders for path in (BASE / folder).rglob('*') if path.is_file()}
    sources = {str(path.relative_to(ROOT)): digest(path) for path in HERE.iterdir() if path.is_file()}
    result = dict(status='passed', checks=checks, goal_complete=False,
                  conclusion='Input-dependent lane transport remains after O3 but reduces to one symbolic lane demand. Independent novelty and sufficient protection gain are unestablished.',
                  artifact_sha256=artifacts, audit_time_source_sha256=sources,
                  note='Main execution sources have contemporaneous v3 snapshots. Later proof/report/audit sources are hashed now. Scalar SMT equivalence is not full SIMD/compiler verification. Initial unsupported cases and failed verification remain archived.')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(dict(status=result['status'], checks=checks,
                          artifact_files=len(artifacts), goal_complete=False)))


if __name__ == '__main__':
    main()
