"""Check saved experiment integrity without rerunning timing measurements."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(folder):
    manifest = read(folder/'manifest.json')
    files = manifest['files']
    names = {x['path'] for x in files}
    assert len(files) == len(names) == 108
    assert sum(not x['recovered'] for x in files) == 54
    hashes = read(folder/'binary-sha256.json')
    assert set(hashes) == names
    assert all(digest(folder/name) == value for name, value in hashes.items())
    audit = read(folder/'audit.json')
    assert all(digest(folder/'sources'/name) == value
               for name, value in audit['source_sha256'].items())
    checks = read(folder/'checks.json')
    assert checks['calls'] == 249804 and checks['files'] == 108
    assert checks['mismatches'] == checks['memory_mismatches'] == 0
    assert {r['path'] for r in checks['records']} == names
    assert all(r['calls'] == 2313 and r['traps'] == 5 and
               r['mismatches'] == r['memory_mismatches'] == 0 for r in checks['records'])
    assert checks['negative_control']['calls'] == 2303
    assert checks['negative_control']['mismatches'] == 1183
    interpreter = read(folder/'interpreter.json')
    assert interpreter['calls'] == 432 and interpreter['mismatches'] == 0
    assert len(interpreter['records']) == 108
    assert all(x['got'] == x['expected'] for x in interpreter['records'])
    analysis = read(folder/'analysis.json')
    assert {r['path'] for r in analysis} == {r['path'] for r in files if not r['recovered']}
    assert all(r['status'] == 'success' and r['dfa_equivalence']['equivalent'] and
               len(r['analysis_samples_ms']) == 9 for r in analysis)
    for r in analysis:
        model = manifest['models'][r['path'].split('.')[0]]
        assert [r['report']['delta'], r['report']['final']] == model['canonical']
    timings = read(folder/'timings.json')
    assert timings['fresh_processes'] == len(timings['records']) == 162
    count = Counter(r['path'] for r in timings['records'])
    assert set(count) == {r['path'] for r in analysis} and set(count.values()) == {3}
    for r in timings['records']:
        assert r['linear_memory_bytes'] == 65536
        assert sorted(x['length'] for x in r['rows']) == [32, 512]
        assert all(x['warmup_calls'] == 200 and x['repetitions'] == 9 and
                   x['calls_per_repetition'] == 200 and len(x['samples_ns_per_call']) == 9
                   for x in r['rows'])
    negative = read(folder/'negative-analysis.json')
    assert all(r['rejected'] for r in negative)
    assert not (folder/'must-not-exist.wasm').exists()
    return dict(folder=str(folder), binaries=len(names), calls=checks['calls'],
                interpreter_calls=interpreter['calls'], recovered=len(analysis),
                fresh_processes=timings['fresh_processes'], negative_controls=len(negative)), hashes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('original', type=Path)
    ap.add_argument('replay', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    first, first_hashes = check(args.original)
    second, second_hashes = check(args.replay)
    assert first_hashes == second_hashes
    algebra = read(args.replay/'algebra-audit.json')
    assert algebra['conditions'] == len(algebra['records']) == 36
    assert algebra['mismatches'] == 0
    assert all(r['conjugacy'] and r['update_initial_output_match'] for r in algebra['records'])
    assert second['negative_controls'] == 3
    snapshot = read(args.replay/'audit.json')['source_sha256']
    for name, value in snapshot.items():
        current = HERE.parent/'connectivity-elimination/prototype.py' if name == 'common-prototype.py' else HERE/name
        assert digest(current) == value, name
    links = 0
    for source in HERE.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
            if target.startswith(('http:', 'https:', '#')):
                continue
            target = target.split('#', 1)[0]
            assert (source.parent/target).exists(), (source.name, target)
            links += 1
    result = dict(experiments=[first, second], identical_binaries=len(first_hashes),
                  algebra_conditions=36, current_sources_match_replay=True,
                  local_document_links=links,
                  scope='Saved evidence integrity only; not a universal equivalence or novelty proof.')
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
