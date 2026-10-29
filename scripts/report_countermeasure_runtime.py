"""Join audited runtime measurements with static records; never run target Wasm."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    if not run.is_relative_to((ROOT / 'results/countermeasures/runtime-runs').resolve()):
        raise ValueError('Run outside runtime result directory')
    # Re-audit the actual inputs, terminal state, isolation and every measurement.
    # This refuses an incomplete run before any comparison or plot is written.
    subprocess.run([sys.executable, str(ROOT / 'scripts/summarize_countermeasure_runtime.py'),
                    str(run)], check=True, cwd=ROOT)
    summary = json.loads((run / 'summary.json').read_text(encoding='utf-8'))
    measurement = json.loads((run / 'outputs/measurement.json').read_text(encoding='utf-8'))
    static_paths = {
        'development': ROOT / 'results/countermeasures/local-normalization/static-comparison.json',
        'alternate-seed-evaluation': ROOT / 'results/countermeasures/seeded-normalization/comparison.json',
    }
    static = {}
    for cohort, path in static_paths.items():
        records = json.loads(path.read_text(encoding='utf-8'))['records']
        static[cohort] = {(r['source'], r['variant']): r for r in records}
    baseline = static['development'][('046dc081-roundtrip', 'unmodified')]
    joined = []
    for row in summary['rows']:
        record = static[row['cohort']][(row['source'], row['method'])]
        if record['sha256'] != row['sha256']:
            raise ValueError('Static/runtime SHA mismatch')
        path = ROOT / row['path']
        if digest(path) != row['sha256'] or path.stat().st_size != record['bytes']:
            raise ValueError('Current artifact differs from audited static/runtime artifact')
        reference = static['development'][('046dc081-roundtrip', row['method'])]
        joined.append(dict(row, bytes=record['bytes'], instruction_count=record['instruction_count'],
            nop_count=record['instructions'].get('nop', 0),
            size_ratio_to_raw_baseline=record['bytes'] / baseline['bytes'],
            instruction_ratio_to_raw_baseline=record['instruction_count'] / baseline['instruction_count'],
            same_bytes_as_equally_processed_baseline=row['sha256'] == reference['sha256']))
    if len(joined) != 72 or len({r['sha256'] for r in joined}) != 23:
        raise ValueError('Unexpected condition/artifact coverage')
    out = run / 'analysis'
    out.mkdir(exist_ok=True)
    result = dict(summary_sha256=digest(run / 'summary.json'),
        measurement_sha256=digest(run / 'outputs/measurement.json'),
        report_script_sha256=digest(Path(__file__)),
        static_sha256={k: digest(v) for k, v in static_paths.items()}, rows=joined,
        limits=('72 labels reuse 23 unique artifacts and six measurements each. '
                'Shared SHA labels are not independent observations. '
                'Min-max is a descriptive range, not a confidence interval. '
                'Rate ratios compare sequential blocks. Static instructions are not executed counts.'))
    (out / 'structure-runtime.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    with (out / 'structure-runtime.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(joined[0]))
        writer.writeheader()
        writer.writerows(joined)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    methods = ['unmodified', 'nop', 'integer-fold', 'both', 'binaryen-local', 'binaryen-O2']
    # Method names come from the frozen plan; fail rather than silently omit a method.
    actual_methods = list(dict.fromkeys(r['method'] for r in joined))
    if set(actual_methods) != set(methods):
        # Preserve the recorded order if the frozen plan uses another optimizer label.
        methods = actual_methods
    sources = list(dict.fromkeys(r['source'] for r in joined if r['cohort'] == 'development'))
    fig, axes = plt.subplots(1, len(sources), figsize=(13, 4), sharey=True, squeeze=False)
    for ax, source in zip(axes[0], sources):
        values = [next(r for r in joined if r['cohort'] == 'development' and
                       r['source'] == source and r['method'] == method) for method in methods]
        for i, row in enumerate(values):
            samples = [s['hashes_per_second'] for s in measurement['samples']
                       if s['sha256'] == row['sha256']]
            ax.scatter([i] * len(samples), samples, s=15, alpha=.65)
            ax.plot([i-.2, i+.2], [row['median_hps']] * 2, color='black', linewidth=1)
        ax.set_xticks(range(len(methods)), methods, rotation=65, ha='right')
        ax.set_title(source, fontsize=9)
        ax.grid(axis='y', alpha=.2)
    axes[0][0].set_ylabel('Completed hashes per second')
    fig.suptitle('Development conditions: six measured blocks per unique SHA')
    fig.tight_layout()
    for extension in ['png', 'svg']:
        fig.savefig(out / ('development-rates.' + extension), dpi=160)
    plt.close(fig)

    # Collapse shared SHA labels for the cross-structure display.
    unique = {}
    for row in joined:
        unique.setdefault(row['sha256'], row)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, key, label in zip(axes,
            ['instruction_ratio_to_raw_baseline', 'size_ratio_to_raw_baseline'],
            ['Static instruction count / raw baseline', 'File bytes / raw baseline']):
        for row in unique.values():
            ax.scatter(row[key], row['baseline_median_rate_ratio'], s=30, alpha=.7)
        ax.axvline(1, color='grey', linewidth=.7)
        ax.axhline(1, color='grey', linewidth=.7)
        ax.set_xlabel(label)
        ax.grid(alpha=.15)
    axes[0].set_ylabel('Median hashes/s / raw baseline')
    fig.suptitle('23 unique SHA artifacts; shared condition labels collapsed')
    fig.tight_layout()
    for extension in ['png', 'svg']:
        fig.savefig(out / ('structure-versus-rate.' + extension), dpi=160)
    plt.close(fig)
    print(json.dumps(dict(joined_conditions=len(joined), unique_artifacts=len(unique), output=str(out))))


if __name__ == '__main__':
    main()
