"""Read saved benchmark logs only; do not execute Wasm or mutate prior results."""
import hashlib
import json
import statistics
from pathlib import Path

root = Path(__file__).resolve().parents[1]
run = root / 'results/countermeasures/runtime-runs/execute-120f528e37424ec6806047c933011eec'
raw = (run / 'outputs/measurement.json').read_bytes()
measurement = json.loads(raw)
plan = json.loads((run / 'inputs/plan.json').read_text())
inspect = json.loads((run / 'container-inspect.json').read_text())
samples = measurement['samples']
rounds = []
for repetition in sorted({s['repetition'] for s in samples}):
    group = [s for s in samples if s['repetition'] == repetition]
    rounds.append({'repetition': repetition, 'n': len(group),
        'median_hps': statistics.median(s['hashes_per_second'] for s in group),
        'order': [s['artifact_id'] for s in group],
        'baseline': [{'position': s['position'], 'hps': s['hashes_per_second'],
                      'started_utc': s['started_utc']}
                     for s in group if s['sha256'] == plan['baseline_sha256']]})
groups = {}
for s in samples:
    groups.setdefault(s['artifact_id'], []).append(s['hashes_per_second'])
first_last = {key: values[-1] / values[0] for key, values in groups.items()}
baseline = [s for s in samples if s['sha256'] == plan['baseline_sha256']]
base_times = [s['started_utc'] for s in baseline]
diagnostic = json.loads((root / 'results/countermeasures/runtime-preparation/input-order-diagnostic.json').read_text())
observations = {}
for item in diagnostic['results']:
    observations.setdefault(item['id'], []).extend(item.get('outputs', [item.get('output')]))
varying = {key: len(set(values)) for key, values in observations.items() if len(set(values)) > 1}
report = {
    'scope': 'Descriptive reanalysis of saved logs only; no new execution or causal identification.',
    'measurement_sha256': hashlib.sha256(raw).hexdigest(),
    'n_samples': len(samples), 'n_sha256': len({s['sha256'] for s in samples}),
    'rounds': rounds,
    'baseline_rates': [s['hashes_per_second'] for s in baseline],
    'baseline_range_pct_of_median': (max(s['hashes_per_second'] for s in baseline)-min(s['hashes_per_second'] for s in baseline))/statistics.median(s['hashes_per_second'] for s in baseline)*100,
    'round1_to_round6_ratio_median_over_artifacts': statistics.median(first_last.values()),
    'artifacts_faster_round6_than_round1': sum(x > 1 for x in first_last.values()),
    'baseline_gap_warning': 'One baseline block per 23-target round; intervening targets are not simultaneous pairs.',
    'host_config': {key: inspect['HostConfig'].get(key) for key in ['NanoCpus', 'CpusetCpus', 'CpuPeriod', 'CpuQuota']},
    'diagnostic_distinct_outputs_if_varying': varying,
    'missing_sample_fields': [key for key in ['cpu_time_us', 'cgroup_cpu_stat', 'jit_tier', 'cpu_affinity', 'frequency'] if not any(key in s for s in samples)],
}
out = root / 'results/additional-experiment-review-20261013'
out.mkdir(exist_ok=True)
(out / 'saved-log-diagnostics.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'rounds'}, indent=2))
print(json.dumps([{'repetition': r['repetition'], 'median_hps': r['median_hps'], 'baseline': r['baseline']} for r in rounds], indent=2))
