"""Freeze runtime candidates and order. Never import a runtime or execute Wasm."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/countermeasures/runtime-preparation'
IMAGE = 'sha256:a05286e66b0f1ca712671db5849229594c92e035bae253362cc8b6d0af4a70b6'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = ['results/countermeasures/local-normalization/static-comparison.json',
             'results/countermeasures/seeded-normalization/comparison.json']
    sources = []
    conditions = []
    grouped = defaultdict(list)
    for cohort, relative in zip(['development', 'alternate-seed-evaluation'], paths):
        source = ROOT/relative
        rows = json.loads(source.read_text(encoding='utf-8'))['records']
        sources.append(dict(path=relative, sha256=sha(source)))
        for row in rows:
            artifact = ROOT/row['path']
            assert artifact.resolve().is_relative_to(ROOT.resolve())
            assert sha(artifact) == row['sha256']
            condition = dict(cohort=cohort, source=row['source'], method=row['variant'],
                             path=row['path'], sha256=row['sha256'])
            conditions.append(condition)
            grouped[row['sha256']].append(condition)
    assert len(conditions) == 72
    vector_path = 'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json'
    public = json.loads((ROOT/vector_path).read_text(encoding='utf-8'))['vectors']
    assert len(public) == 5
    for vector in public:
        assert len(bytes.fromhex(vector['hex'])) <= 256
        assert len(bytes.fromhex(vector['expected'])) == 32
    additional = []
    for length in [1, 8, 32, 76, 128, 255]:
        data = b''.join(hashlib.sha256(f'countermeasure-cn0-20261010:{length}:{i}'.encode()).digest() for i in range(8))[:length]
        additional.append(dict(id=f'differential-length-{length}', hex=data.hex(),
                               expected=None, oracle='unmodified SWAMPED baseline; differential comparison only'))
    for index in range(6):
        data = bytearray.fromhex(public[index % 5]['hex'])
        assert len(data) >= 43
        data[39:43] = (index * 0x1020304 + 1).to_bytes(4, 'little')
        additional.append(dict(id=f'differential-nonce-{index}', hex=data.hex(),
                               expected=None, oracle='unmodified SWAMPED baseline; differential comparison only'))
    artifacts = [dict(id=f'artifact-{i:03}', sha256=digest, path=labels[0]['path'],
                      conditions=labels) for i, (digest, labels) in enumerate(sorted(grouped.items()))]
    baseline = next(c for c in conditions if c['cohort'] == 'development' and
                    c['source'] == '046dc081-roundtrip' and c['method'] == 'unmodified')
    schedule = []
    for repetition in range(6):
        rotated = artifacts[repetition:] + artifacts[:repetition]
        schedule.extend(dict(repetition=repetition+1, position=i, artifact_id=a['id'],
                             sha256=a['sha256']) for i, a in enumerate(rotated))
    host = 'experiments/runtime-reference/swamped-host.cjs'
    plan = dict(status='prepared-not-executed', target_wasm_executed=False,
                professor_permission_confirmed=False, conditions=conditions, artifacts=artifacts,
                source_manifests=sources, public_vector_source=dict(path=vector_path, sha256=sha(ROOT/vector_path)),
                public_vectors=public, additional_vectors=additional, baseline_sha256=baseline['sha256'],
                host=dict(path=host, sha256=sha(ROOT/host), initialization_clock_ms=1700000000500,
                          input_allocation_bytes=256, output_bytes=32, memory_mib=16),
                environment=dict(image=IMAGE, intended_node='v18.20.4', intended_v8='10.2.154.26-node.37',
                                 actual_runtime_unverified=True, network='none', workers=1,
                                 cpu_limit=1, memory_limit_mib=1024, pids_limit=64,
                                 read_only_input=True, read_only_root=True, no_new_privileges=True,
                                 cap_drop='ALL', maximum_wall_seconds=7200),
                measurement=dict(warmup_seconds=3, minimum_block_seconds=30, repetitions=6,
                                 schedule=schedule, throughput_input='five public cn/0 vectors cyclically',
                                 initialization_in_timing=False,
                                 pre_and_post_checks='all five public vectors; final block output expected',
                                 additional_checks='before throughput: baseline and every unique artifact, two input orders',
                                 failure_policy='stop and preserve partial logs; no successful speed aggregate on mismatch'),
                minimum_timed_seconds=len(schedule)*30, nominal_warmup_plus_timed_seconds=len(schedule)*33,
                limits=['Shared SHA across labels is measured once per round and mapped back to all labels.',
                        'All inputs use one underlying mining implementation; not independent malware families.',
                        'Additional expected hashes are not public reference values; baseline agreement is differential evidence.',
                        'No whole-module equivalence is inferred from finite inputs or byte identity.',
                        'Measured CPU host must be recorded at execution, not copied from historical logs.',
                        'This plan does not grant permission or prove isolation; a reviewed launcher is still required.'])
    (OUT/'plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    report = dict(conditions=len(conditions), unique_artifacts=len(artifacts), public_vectors=len(public),
                  additional_vectors=len(additional), planned_blocks=len(schedule),
                  plan_sha256=sha(OUT/'plan.json'), preparer_sha256=sha(Path(__file__)),
                  files_sha_verified=True, target_wasm_executed=False, runtime_results_available=False)
    (OUT/'preparation-checks.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
