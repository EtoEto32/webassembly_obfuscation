"""Join completed repeated runtime measurements to build and mechanism evidence."""
import csv
import json
import os
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'data/matplotlib-cache'))

def main():
    report = json.loads((OUT / 'xmr-repeated-throughput-20261008.json').read_text())
    audit = json.loads((OUT / 'runtime-mechanism-audit.json').read_text())
    assert report.get('finished_utc') and len(report['samples']) == 15
    assert all(s['final_output_matches'] and s['final_nonce_unchanged'] for s in report['samples'])
    order = ['xmr-wasm', 'xmr-wasm-emccobf-flattening', 'xmr-wasm-emccobf-split',
             'xmr-wasm-emccobf-substitution', 'xmr-wasm-emccobf-boguscf']
    rows = []
    for name in order:
        evidence = next(x for x in audit['modules'] if x['declared_directory'] == name)
        samples = [s for s in report['samples'] if s['method'] == name]
        assert sorted(s['repetition'] for s in samples) == [1, 2, 3]
        assert all(s['sha256'] == evidence['sha256'] for s in samples)
        rates = [s['hashes_per_second'] for s in samples]
        rows.append(dict(method=name, sha256=evidence['sha256'], repetitions=len(samples),
                         median_hps=statistics.median(rates), min_hps=min(rates), max_hps=max(rates),
                         bytes=evidence['bytes'], instructions=evidence['instructions'],
                         build_flags=' '.join(evidence['build_flags']),
                         optimization_flags=' '.join(evidence['optimization_flags']),
                         mechanism_status=evidence['mechanism_status'],
                         public_vectors_checked=evidence['public_vectors_checked']))
    for row in rows:
        row['descriptive_throughput_ratio'] = row['median_hps'] / rows[0]['median_hps']
        row['size_ratio'] = row['bytes'] / rows[0]['bytes']
        row['instruction_ratio'] = row['instructions'] / rows[0]['instructions']
        row['causal_obfuscation_effect_established'] = False
    with (OUT / 'xmr-repeated-summary.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels = ['Reference', 'Flattening', 'Split (decl.)', 'Substitution (decl.)', 'Boguscf (decl.)\n-O2 confound']
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.5), layout='constrained')
    med = [r['median_hps'] for r in rows]
    axes[0].bar(range(5), med, color=['#4477AA']*4+['#CCBB44'])
    axes[0].errorbar(range(5), med, yerr=[[r['median_hps']-r['min_hps'] for r in rows],
                                          [r['max_hps']-r['median_hps'] for r in rows]],
                     fmt='none', color='black', capsize=3)
    axes[0].set_ylabel('Hashes/s: median and min/max (3 runs)')
    for key, label, marker in [('size_ratio', 'File size', 'o'), ('instruction_ratio', 'Instructions', 's'),
                               ('descriptive_throughput_ratio', 'Throughput (descriptive)', '^')]:
        axes[1].plot(range(5), [r[key] for r in rows], marker+'-', label=label)
    axes[1].axhline(1, color='grey', lw=.7)
    axes[1].set_ylabel('Ratio to reference artifact'); axes[1].legend(fontsize=8)
    for ax in axes:
        ax.set_xticks(range(5), labels, rotation=20, ha='right', fontsize=8)
    fig.savefig(OUT / 'xmr-repeated-throughput.pdf')
    fig.savefig(OUT / 'xmr-repeated-throughput.png', dpi=160)
    plt.close(fig)
    (OUT / 'xmr-repeated-summary.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(json.dumps(rows, indent=2))

if __name__ == '__main__':
    main()
