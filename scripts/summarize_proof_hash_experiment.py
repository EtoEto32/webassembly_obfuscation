"""Summarize actual preliminary measurements and join existing static analysis."""
import csv
import json
import statistics
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'data/matplotlib-cache'))


def main():
    report = json.loads((OUT / 'hash-throughput-preliminary-20261007-retry.json').read_text())
    if 'finished_utc' not in report or len(report['benchmark']['samples']) != 15:
        raise ValueError('Do not summarize incomplete measurements as complete')
    rows = []
    baseline = json.loads((ROOT / 'data/analysis-v2' / (report['results'][0]['sha256'] + '.json')).read_text())
    for module in report['results']:
        samples = [s for s in report['benchmark']['samples'] if s['sha256'] == module['sha256']]
        if not samples:
            continue
        static = json.loads((ROOT / 'data/analysis-v2' / (module['sha256'] + '.json')).read_text())
        rates = [s['hashes_per_second'] for s in samples]
        rows.append(dict(method=module['method'], sha256=module['sha256'], repetitions=len(rates),
                         median_hps=statistics.median(rates), min_hps=min(rates), max_hps=max(rates),
                         bytes=static['bytes'], instructions=static['instruction_count'],
                         size_ratio=static['bytes']/baseline['bytes'],
                         instruction_ratio=static['instruction_count']/baseline['instruction_count'],
                         br_table_in_loop=static['br_table_in_loop_count'],
                         matched_reference_vectors=len(module['outputs'])))
    for row in rows:
        row['throughput_ratio'] = row['median_hps'] / rows[0]['median_hps']
    with (OUT / 'preliminary-summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels = ['Reference dir.', 'flattening dir.', 'split dir.', 'substitution dir.', 'boguscf dir.']
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), layout='constrained')
    med = [r['median_hps'] for r in rows]
    axes[0].bar(range(len(rows)), med, color='#4477AA')
    axes[0].errorbar(range(len(rows)), med,
                     yerr=[[r['median_hps']-r['min_hps'] for r in rows],
                           [r['max_hps']-r['median_hps'] for r in rows]], fmt='none', color='black', capsize=3)
    axes[0].set_ylabel('Hashes/s (median; bars show min/max)')
    axes[1].plot(range(len(rows)), [r['size_ratio'] for r in rows], 'o-', label='File size')
    axes[1].plot(range(len(rows)), [r['instruction_ratio'] for r in rows], 's-', label='Instructions')
    axes[1].plot(range(len(rows)), [r['throughput_ratio'] for r in rows], '^-', label='Hash throughput')
    axes[1].axhline(1, color='grey', lw=.7)
    axes[1].set_ylabel('Ratio to reference artifact'); axes[1].legend(fontsize=8)
    for ax in axes:
        ax.set_xticks(range(len(rows)), labels, rotation=25, ha='right', fontsize=8)
    fig.savefig(OUT / 'preliminary-throughput.pdf')
    fig.savefig(OUT / 'preliminary-throughput.png', dpi=160)
    plt.close(fig)
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
