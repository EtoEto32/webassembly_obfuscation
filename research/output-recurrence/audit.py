"""Audit saved artifacts and counts; does not rerun performance measurements."""
import argparse
import hashlib
import json
from pathlib import Path
import re

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
    v1, v2 = 'output-recurrence-v1', 'output-recurrence-v2'
    summary = read(v2, 'summary.json')
    manifest = read(v2, 'manifest.json')
    assert len(summary) == len(manifest['files']) == 32
    assert len({r['path'] for r in summary}) == 32
    for row in summary:
        path = BASE / v2 / row['path']
        assert path.stat().st_size == row['bytes']
        assert digest(path) == row['sha256']
        assert path.read_bytes() == (BASE / v1 / row['path']).read_bytes()
    replay = read(v2, 'replay.json')
    assert len(replay) == 32 and all(replay.values())
    checks['binary_hashes_and_byte_replay'] = 32
    hashes = read(v2, 'environment.json')['source_sha256']
    for path, expected in hashes.items():
        source = ROOT / path
        snapshot = BASE / v2 / 'sources' / (source.parent.name + '_' + source.name)
        assert digest(source) == digest(snapshot) == expected, path
    checks['execution_source_hashes_match'] = len(hashes)
    correct = read(v2, 'correctness.json')
    extra = read('output-recurrence-verify-v1/noninjective', 'correctness.json')
    for value, binaries, calls, traps in [(correct, 32, 66080, 9216), (extra, 9, 18585, 2592)]:
        assert value['binaries'] == binaries and value['calls'] == calls
        assert value['traps'] == traps and value['mismatches'] == 0
        assert sum(r['calls'] for r in value['records']) == calls
        assert sum(r['traps'] for r in value['records']) == traps
    checks['native_correctness_calls'] = correct['calls'] + extra['calls']
    checks['native_traps'] = correct['traps'] + extra['traps']
    interp = read('output-recurrence-verify-v1', 'interpreter.json')
    assert (interp['calls'], interp['memory_probes'], interp['mismatches']) == (224, 128, 0)
    checks['interpreter_calls'] = interp['calls']
    algebra = read('output-recurrence-verify-v1', 'algebra.json')
    assert algebra['state_checks'] == 89904 and algebra['mismatches'] == 0
    checks['local_algebra_states'] = algebra['state_checks']
    collision_dir = BASE / 'output-recurrence-verify-v1/noninjective'
    collisions = read('output-recurrence-verify-v1/noninjective', 'collisions.json')
    assert len(collisions) == 3
    for row in collisions:
        assert row['distinct_initial_y'] and row['distinct_Q_constant'] and row['identical_history_bytes']
        assert (collision_dir / (row['model'] + '.history.wasm')).read_bytes() == (BASE / v2 / (row['model'] + '.history.raw.wasm')).read_bytes()
    checks['noninjective_binary_collisions'] = len(collisions)
    controls = read('output-recurrence-verify-v1', 'controls.json')
    assert sum('rejected' in r for r in controls) == 4
    wrong = next(r for r in controls if r['name'] == 'wrong_previous_input')
    assert wrong['values'][0] != wrong['values'][1]
    checks['refused_valid_outside_profile'] = 4
    checks['wrong_recurrence_detected'] = True
    recoveries = read(v2, 'analysis.json')
    assert len(recoveries) == 8 and all(r['same_as_quotient_bytes'] for r in recoveries)
    checks['recovered_quotient_binaries'] = 8
    compare = read('output-recurrence-compare-v1', 'comparison.json')
    assert len(compare) == 24
    for row in compare:
        canonical = BASE / 'output-recurrence-compare-v1' / (Path(row['path']).stem + '.canonical.wasm')
        reference = BASE / v2 / (row['model'] + '.quotient.raw.wasm')
        assert row['same_as_quotient'] and canonical.read_bytes() == reference.read_bytes()
    checks['equal_budget_canonical_matches'] = 24
    bench = read(v2, 'benchmark.json')
    assert len(bench) == 72
    for row in summary:
        if 'kind' in row:
            continue
        group = [b for b in bench if b['path'] == row['path']]
        assert len(group) == 3 and {b['repeat'] for b in group} == {0, 1, 2}
        for b in group:
            assert (b['warmup'], b['repetitions'], b['calls_per_sample'], b['input_length']) == (10000, 11, 3000, 64)
            assert len(b['samples_ns']) == 11
    checks['fresh_benchmark_processes'] = len(bench)
    ext = read('output-recurrence-extension-v1', 'results.json')
    assert ext['polynomial_nonzero_b_checks'] + ext['zero_b_checks'] == 97380
    assert ext['polynomial_mismatches'] == 0
    assert (ext['rotation_calls'], ext['rotation_counterexamples']) == (62, 31)
    for witness in ext['witnesses']:
        assert witness['before'][0] == witness['before'][1]
        assert witness['after'][0] != witness['after'][1]
    checks['polynomial_extension_checks'] = 97380
    checks['actual_wasm_rotation_counterexamples'] = 31
    local_links = 0
    for path in HERE.glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if link.startswith(('http:', 'https:', '#')):
                continue
            target = link.split('#', 1)[0]
            assert (path.parent / target).exists(), (path, target)
            local_links += 1
    checks['existing_local_document_links'] = local_links
    record_hashes = {}
    for directory in [v1, v2, 'output-recurrence-verify-v1', 'output-recurrence-compare-v1', 'output-recurrence-extension-v1']:
        for path in (BASE / directory).rglob('*'):
            if path.is_file():
                record_hashes[str(path.relative_to(ROOT))] = digest(path)
    current_sources = {str(path.relative_to(ROOT)): digest(path) for path in HERE.iterdir() if path.is_file()}
    result = dict(status='passed', checks=checks, goal_complete=False,
                  conclusion='Restricted state elimination works; cheap equivalent realization defeats the protection claim. No novel effective main invention established.',
                  artifact_sha256=record_hashes, audit_time_source_sha256=current_sources,
                  note='The extension source hash is captured at audit time. Main v2 sources have contemporaneous run snapshots. No new runtime measurements are performed by this audit.')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(dict(status=result['status'], checks=checks, artifact_files=len(record_hashes), goal_complete=False)))

if __name__ == '__main__':
    main()
