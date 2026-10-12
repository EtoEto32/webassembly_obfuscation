"""Read-only audit of the frozen plan, no runtime loading or Wasm execution."""
import json
import hashlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/countermeasures/runtime-preparation'


def main():
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    plan = json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
    preparation = json.loads((OUT/'preparation-checks.json').read_text(encoding='utf-8'))
    assert preparation['plan_sha256'] == sha(OUT/'plan.json')
    for entry in plan['source_manifests']+[plan['public_vector_source'], plan['host']]:
        path = (ROOT/entry['path']).resolve()
        assert path.is_relative_to(ROOT.resolve()) and sha(path) == entry['sha256']
    artifacts = {a['id']: a for a in plan['artifacts']}
    assert len(artifacts) == len({a['sha256'] for a in artifacts.values()}) == 23
    labels = []
    for artifact in artifacts.values():
        assert sha(ROOT/artifact['path']) == artifact['sha256']
        for condition in artifact['conditions']:
            assert sha(ROOT/condition['path']) == condition['sha256'] == artifact['sha256']
            labels.append((condition['cohort'],condition['source'],condition['method']))
    assert len(labels) == len(set(labels)) == len(plan['conditions']) == 72
    assert set(labels) == {(c['cohort'],c['source'],c['method']) for c in plan['conditions']}
    for round_index in range(1,7):
        rows = [s for s in plan['measurement']['schedule'] if s['repetition'] == round_index]
        assert len(rows) == 23
        assert Counter(r['artifact_id'] for r in rows) == Counter(artifacts.keys())
        assert sorted(r['position'] for r in rows) == list(range(23))
        for row in rows:
            assert row['sha256'] == artifacts[row['artifact_id']]['sha256']
    assert len({v['hex'] for v in plan['additional_vectors']}) == 12
    assert all(0 < len(bytes.fromhex(v['hex'])) <= plan['host']['input_allocation_bytes']
               for v in plan['public_vectors']+plan['additional_vectors'])
    assert all(v['expected'] is None for v in plan['additional_vectors'])
    assert all(len(bytes.fromhex(v['expected'])) == 32 for v in plan['public_vectors'])
    assert plan['professor_permission_confirmed'] is False
    assert plan['target_wasm_executed'] is False
    report = dict(plan_sha256=sha(OUT/'plan.json'), checker_sha256=sha(Path(__file__)),
                  artifact_groups=23, condition_labels=72, verified_rounds=6, blocks=138,
                  bounded_additional_inputs=12, target_wasm_executed=False,
                  remaining=['Explicit professor permission confirmation',
                             'Reviewed isolated launcher and actual environment verification',
                             'New output and throughput logs; aggregation and paper reflection'])
    (OUT/'plan-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
