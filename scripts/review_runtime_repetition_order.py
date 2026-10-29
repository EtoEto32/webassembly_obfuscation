"""Analyze saved 30-second blocks and completion order; no hashing execution."""
import csv
import hashlib
import json
import os
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/runtime-mining/cross-dataset'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'data/matplotlib-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

specs = [('xmr', 'proof-of-theft/xmr-repeated-throughput-20261008.json', 'method', 'xmr-wasm'),
         ('swamped', 'swamped/controlled-pair-repeated-throughput.json', 'name', '046dc081-roundtrip')]
reports, csv_rows = [], []
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
for axis, (label, name, field, reference) in zip(axes, specs):
    path = BASE/name
    raw = json.loads(path.read_text())
    samples = raw['samples']
    timestamps = [datetime.fromisoformat(s['finished_utc'].replace('Z', '+00:00')) for s in samples]
    assert timestamps == sorted(timestamps)
    baseline = {s['repetition']:s for s in samples if s[field] == reference}
    assert set(baseline) == {1,2,3}
    names = list(dict.fromkeys(s[field] for s in samples))
    rounds = []
    comparisons = []
    for repetition in range(1,4):
        group = [s for s in samples if s['repetition'] == repetition]
        assert set(s[field] for s in group) == set(names) and len(group) == len(names)
        rounds.append(dict(repetition=repetition, order=[s[field] for s in group]))
    for method in names:
        group = [s for s in samples if s[field] == method]
        ratios, gaps = [], []
        x, y = [], []
        for sample in group:
            assert sample['final_output_matches']
            recomputed = sample['count']*1000/sample['elapsed_ms']
            assert abs(recomputed-sample['hashes_per_second']) < 1e-9
            base = baseline[sample['repetition']]
            ratio = recomputed/base['hashes_per_second']
            gap = (datetime.fromisoformat(sample['finished_utc'].replace('Z','+00:00'))-
                   datetime.fromisoformat(base['finished_utc'].replace('Z','+00:00'))).total_seconds()
            ratios.append(ratio);gaps.append(gap)
            elapsed = (datetime.fromisoformat(sample['finished_utc'].replace('Z','+00:00'))-timestamps[0]).total_seconds()
            x.append(elapsed/60);y.append(recomputed)
            csv_rows.append(dict(experiment=label,method=method,repetition=sample['repetition'],
                completion_utc=sample['finished_utc'],completion_minutes_from_first=elapsed/60,
                hashes_per_second=recomputed,within_round_reference_ratio=ratio,
                completion_gap_from_round_reference_seconds=gap))
        display = method.replace('xmr-wasm-emccobf-', '').replace('046dc081-', '')
        if display == 'boguscf':display += ' (-O2)'
        axis.plot(x,y,'o-',label=display,linewidth=1,markersize=4)
        if method == reference:
            continue
        comparisons.append(dict(method=method,within_round_ratios=ratios,
            ratio_min=min(ratios),ratio_median=statistics.median(ratios),ratio_max=max(ratios),
            direction=['below reference' if r<1 else 'above reference' if r>1 else 'equal' for r in ratios],
            completion_gaps_seconds=gaps,
            median_of_rates_ratio=statistics.median(y)/statistics.median([s['hashes_per_second'] for s in baseline.values()])))
    base_rates = [baseline[r]['hashes_per_second'] for r in range(1,4)]
    reports.append(dict(experiment=label,raw_report=name,raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        round_orders=rounds,reference_rates=base_rates,reference_last_to_first_ratio=base_rates[-1]/base_rates[0],
        comparisons=comparisons))
    axis.set(title=label, xlabel='Recorded completion time from first block (min)',ylabel='Hashing throughput (H/s)')
    axis.grid(alpha=.25);axis.legend(fontsize=8)
fig.tight_layout()
fig.savefig(BASE/'repetition-order-review.pdf',bbox_inches='tight')
fig.savefig(BASE/'repetition-order-review.png',dpi=180,bbox_inches='tight')
plt.close(fig)
report = dict(experiments=reports,
    scope='Descriptive analysis of saved 30-second blocks grouped by recorded repetition; not new measurements.',
    definitions=dict(within_round_ratio='Variant rate divided by reference rate in the same repetition group.',
                     median_of_rates_ratio='Ratio of separate variant and reference medians; generally differs from median of within-round ratios.'),
    limitations=['Blocks are sequential, not simultaneous; grouping within a round does not remove time drift or establish matched independent pairs.',
                 'Only three rounds; no significance, equivalence, confidence-interval, or population-effect claim.',
                 'Completion timestamps include work after the timed loop; they are not exact timed-loop starts or durations.',
                 'Warming, frequency changes, host load, and JIT effects were not separately measured; the cause of drift is unresolved.',
                 'The xmr sequence covers three of five cyclic orders; SWAMPED covers all three cyclic orders, not all permutations.'])
(BASE/'repetition-order-review.json').write_text(json.dumps(report,indent=2)+'\n')
with (BASE/'repetition-order-review.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(csv_rows[0]));writer.writeheader();writer.writerows(csv_rows)
print(json.dumps([dict(experiment=r['experiment'],reference_last_to_first_ratio=r['reference_last_to_first_ratio'],
    comparisons=[dict(method=c['method'],range=[c['ratio_min'],c['ratio_max']],directions=c['direction']) for c in r['comparisons']]) for r in reports],indent=2))
