"""Audit a complete isolated run before producing any throughput aggregates."""
import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review_measurement(plan, report):
    require(report.get('status') == 'complete', 'Measurement is incomplete or failed')
    require(not report.get('failed_check') and not report.get('error'), 'Failure evidence present')
    require(report['node'] == plan['environment']['intended_node'] and
            report['v8'] == plan['environment']['intended_v8'], 'Runtime mismatch')
    require(report['image_id'] == plan['environment']['image'], 'Image mismatch')
    require(bool(report['cpu_model']), 'CPU metadata missing')
    public = plan['public_vectors']
    oracle = report['baseline_oracle']['additional_outputs']
    require(set(oracle) == {v['id'] for v in plan['additional_vectors']}, 'Additional oracle coverage')
    require(all(re.fullmatch('[a-f0-9]{64}', v) for v in oracle.values()), 'Invalid oracle output')

    def check(rows, vectors, expected=None):
        require(len(rows) == len(vectors), 'Input checks missing')
        for row, vector in zip(rows, vectors):
            wanted = expected[vector['id']] if expected else vector['expected']
            require(row['id'] == vector['id'] and row['matches'] is True and
                    row['actual'] == row['expected'] == wanted, 'Input output or order mismatch')

    check(report['baseline_oracle']['public_checks'], public)
    require(len(report['fresh_additional_checks']) == len(plan['artifacts']), 'Fresh-context coverage')
    for row, artifact in zip(report['fresh_additional_checks'], plan['artifacts']):
        require(row['artifact_id']==artifact['id'], 'Fresh-context artifact order')
        check(row['checks'],plan['additional_vectors'],report['baseline_oracle']['fresh_additional_outputs'])
    for key, additional in [('public_checks', False), ('additional_checks', True)]:
        rows = report[key]
        require(len(rows) == 2 * len(plan['artifacts']), 'Artifact check coverage')
        expected_keys = [(a['id'], reverse) for a in plan['artifacts'] for reverse in [False, True]]
        require([(r['artifact_id'], r['reverse']) for r in rows] == expected_keys, 'Artifact check order')
        for row in rows:
            vectors = plan['additional_vectors'] if additional else public
            if additional and row['reverse']:
                vectors = list(reversed(vectors))
            expected = report['baseline_oracle']['additional_outputs_by_order']['reverse' if row['reverse'] else 'forward'] if additional else None
            check(row['checks'], vectors, expected)
    samples = report['samples']
    schedule = plan['measurement']['schedule']
    require(len(samples) == len(schedule), 'Scheduled blocks missing')
    previous_finish = None
    for row, intended in zip(samples, schedule):
        require(all(row[k] == v for k, v in intended.items()), 'Schedule or SHA mismatch')
        require(type(row['count']) is int and row['count'] > 0, 'Invalid completed hash count')
        require(type(row['warmup_count']) is int and row['warmup_count'] > 0 and
                math.isfinite(row['warmup_elapsed_ms']) and
                row['warmup_elapsed_ms'] >= plan['measurement']['warmup_seconds']*1000,
                'Warmup evidence missing or short')
        elapsed = row['elapsed_ms']
        require(math.isfinite(elapsed) and elapsed >= plan['measurement']['minimum_block_seconds'] * 1000,
                'Invalid or short measured block')
        rate = row['count'] * 1000 / elapsed
        require(math.isclose(row['hashes_per_second'], rate, rel_tol=1e-12), 'Rate arithmetic mismatch')
        last = public[(row['count'] - 1) % len(public)]
        require(row['final_output'] == row['final_expected'] == last['expected'], 'Final output mismatch')
        check(row['pre_checks'], public)
        check(row['post_checks'], public)
        require(bool(row.get('started_utc')) and bool(row.get('finished_utc')), 'Block timestamps missing')
        start = datetime.fromisoformat(row['started_utc'].replace('Z','+00:00'))
        finish = datetime.fromisoformat(row['finished_utc'].replace('Z','+00:00'))
        require(start.tzinfo is not None and finish.tzinfo is not None and finish > start, 'Invalid UTC interval')
        require((finish-start).total_seconds()*1000 + 2 >= elapsed, 'Elapsed exceeds UTC interval')
        require(previous_finish is None or start >= previous_finish, 'Overlapping sequential blocks')
        previous_finish = finish
    return samples


def aggregate(plan, samples):
    by_sha = {}
    for artifact in plan['artifacts']:
        rows = [r for r in samples if r['sha256'] == artifact['sha256']]
        require(len(rows) == plan['measurement']['repetitions'], 'Wrong repetition count')
        rates = [r['count'] * 1000 / r['elapsed_ms'] for r in rows]
        by_sha[artifact['sha256']] = dict(median_hps=statistics.median(rates), min_hps=min(rates),
            max_hps=max(rates), repetitions=len(rows), by_round={r['repetition']: rate for r, rate in zip(rows, rates)})
    baseline_labels = [c for c in plan['conditions'] if c['cohort'] == 'development' and
                       c['source'] == '046dc081-roundtrip']
    rows = []
    for condition in plan['conditions']:
        value = by_sha[condition['sha256']]
        equal_sha = next(c['sha256'] for c in baseline_labels if c['method'] == condition['method'])
        raw_sha = next(c['sha256'] for c in plan['conditions'] if c['cohort'] == condition['cohort'] and
                       c['source'] == condition['source'] and c['method'] == 'unmodified')
        row = dict(condition, **{k: value[k] for k in ['median_hps','min_hps','max_hps','repetitions']})
        for name, reference_sha in [('baseline', plan['baseline_sha256']),
                                    ('equally_processed_baseline', equal_sha), ('same_input_unmodified', raw_sha)]:
            reference = by_sha[reference_sha]
            ratios = [rate/reference['by_round'][rep] for rep, rate in value['by_round'].items()]
            row[name+'_median_rate_ratio'] = value['median_hps']/reference['median_hps']
            row[name+'_round_ratio_median'] = statistics.median(ratios)
            row[name+'_round_ratio_min'] = min(ratios)
            row[name+'_round_ratio_max'] = max(ratios)
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    require(run.is_relative_to((ROOT/'results/countermeasures/runtime-runs').resolve()), 'Run outside result directory')
    plan_path = run/'inputs/plan.json'
    report_path = run/'outputs/measurement.json'
    # A probe lacks measurement.json and must never be converted into rates.
    report = json.loads(report_path.read_text(encoding='utf-8'))
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    require(report['plan_sha256'] == sha(plan_path), 'Plan digest mismatch')
    require(report['runner_sha256'] == sha(run/'inputs/runner.cjs'), 'Runner digest mismatch')
    require(report['host_sha256'] == sha(run/'inputs/swamped-host.cjs') == plan['host']['sha256'], 'Host digest mismatch')
    require(report['permission_sha256'] == sha(run/'inputs/permission.json'), 'Permission evidence digest mismatch')
    permission = json.loads((run/'inputs/permission.json').read_text(encoding='utf-8'))
    require(permission.get('confirmed') is True and permission.get('plan_sha256') == sha(plan_path) and
            bool(permission.get('user_statement')) and bool(permission.get('confirmed_at')), 'Permission record invalid')
    for artifact in plan['artifacts']:
        require(sha(run/'inputs'/(artifact['sha256']+'.wasm')) == artifact['sha256'], 'Artifact digest mismatch')
    completion = json.loads((run/'completion.json').read_text(encoding='utf-8'))
    state = completion['state']
    require(completion['exit_code'] == state['ExitCode'] == 0 and not state['Running'] and not state['OOMKilled'],
            'Container unsuccessful or still running')
    metadata = json.loads((run/'container-inspect.json').read_text(encoding='utf-8'))
    host = metadata['HostConfig']
    require(host['NetworkMode'] == 'none' and host['ReadonlyRootfs'] and host['NanoCpus'] == 1_000_000_000 and
            host['Memory'] == host['MemorySwap'] == 1024**3 and host['PidsLimit'] == 64, 'Isolation mismatch')
    require(metadata['Image'] == plan['environment']['image'] and metadata['Config']['User'] == '10001:10001' and
            'ALL' in host['CapDrop'] and any(s.startswith('no-new-privileges') for s in host['SecurityOpt']),
            'Image, user or capability restrictions mismatch')
    mounts = {m['Destination']:m for m in metadata['Mounts']}
    require(not mounts['/inputs']['RW'] and mounts['/outputs']['RW'], 'Mount restrictions mismatch')
    samples = review_measurement(plan, report)
    rows = aggregate(plan, samples)
    summary = dict(plan_sha256=sha(plan_path), measurement_sha256=sha(report_path),
                   aggregator_sha256=sha(Path(__file__)), blocks=len(samples), unique_artifacts=len(plan['artifacts']),
                   label_conditions=len(rows), rows=rows,
                   limits='Labels sharing SHA reuse the same six measurements. Round ratios are sequential, not simultaneous pairs. Min-max is not a confidence interval. Additional checks use a differential baseline oracle.')
    # Write only after all checks and aggregation succeed.
    (run/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    with (run/'summary.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(dict(verified_blocks=len(samples), unique_artifacts=len(plan['artifacts']), label_conditions=len(rows))))


if __name__ == '__main__':
    main()
