"""Compare declared completed runs. No synthetic data or missing-run substitution."""
import argparse
import csv
import json
import os
from pathlib import Path
from analyze_reference import summarize


def compare(manifest):
    with manifest.open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError('No runs provided; no measurement figure can be generated')
    expected = {'run_id','run_directory','input_sha256','baseline_sha256','program','release','method'}
    if not expected <= set(rows[0]):
        raise ValueError('Manifest is missing run identity or pairing fields')
    summaries = {}
    for row in rows:
        if row['run_id'] in summaries:
            raise ValueError('Duplicate run identifier')
        directory = Path(row['run_directory'])
        if not directory.is_absolute():
            directory = manifest.parent / directory
        result = {'row':row,'directory':directory,'summary':None,'error':None}
        try:
            # The runner must preserve the measured input identity.
            metadata = json.loads((directory / 'run-metadata.json').read_text(encoding='utf-8-sig'))
            if metadata['input_sha256'] != row['input_sha256']:
                raise ValueError('Measured input differs from comparison manifest')
            if metadata.get('synthetic') is not False:
                raise ValueError('Run is not explicitly recorded as a real measurement')
            if (directory / 'collection-failure.json').exists():
                raise ValueError('Collection failed; do not summarize as a completed run')
            result['summary'] = summarize(directory)
        except (OSError, ValueError, KeyError) as error:
            result['error'] = str(error)
        summaries[row['run_id']] = result
    comparisons = []
    for item in summaries.values():
        row = item['row']
        parents = [parent for parent in summaries.values()
                   if parent['row']['input_sha256'] == row['baseline_sha256']
                   and parent['row']['program'] == row['program']
                   and parent['row']['release'] == row['release']
                   and parent['row']['method'] in ('unobfuscated', 'original')]
        if len(parents) != 1:
            raise ValueError('Missing or ambiguous baseline run for ' + row['run_id'])
        parent = parents[0]
        summary, baseline = item['summary'], parent['summary']
        speed = summary['reference_filtered_median_hps'] if summary else None
        normal_speed = baseline['reference_filtered_median_hps'] if baseline else None
        comparisons.append({**row, 'error':item['error'],
            'reference_filtered_median_hps':speed,
            'speed_ratio_to_baseline':speed / normal_speed if speed is not None and normal_speed else None,
            'submitted':summary['submitted'] if summary else None,
            'accepted':summary['accepted'] if summary else None,
            'rejected':summary['rejected'] if summary else None,
            'pool_correctness':summary['pool_correctness'] if summary else 'not established',
            'raw_rate_samples':summary['rate_samples'] if summary else 0,
            'excluded_rate_samples':summary['reference_excluded_samples'] if summary else None})
    return comparisons, summaries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    comparisons, runs = compare(args.manifest.resolve())
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / 'runtime-comparison.csv').open('w',encoding='utf-8',newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)
    # Use actual observed raw rates; filter affects table values only.
    observed = [(key, value['summary']['rates']) for key,value in runs.items() if value['summary']]
    if observed:
        os.environ['MPLCONFIGDIR'] = str((args.output / '.matplotlib-cache').resolve())
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        figure, axis = plt.subplots(figsize=(8,max(3,0.35*len(observed))))
        variable = [(index,rates) for index,(_,rates) in enumerate(observed,1)
                    if len(set(rates)) > 1]
        if variable:
            axis.violinplot([rates for _,rates in variable], positions=[index for index,_ in variable],
                            vert=False, showmeans=True, showmedians=True)
        # A constant observed series has no density estimate. Show its actual
        # value, without jitter or random values manufactured for the plot.
        for index,(_,rates) in enumerate(observed,1):
            if len(set(rates)) == 1:
                axis.plot([rates[0]],[index],marker='|',markersize=16,color='black')
        axis.set_yticks(range(1,len(observed)+1), [key for key,_ in observed])
        axis.set_xlabel('Hashes per nominal one-second interval (raw observations)')
        figure.tight_layout()
        figure.savefig(args.output / 'hash-rate-distributions.pdf')
        figure.savefig(args.output / 'hash-rate-distributions.png',dpi=200)
        plt.close(figure)
    (args.output / 'comparison-status.json').write_text(json.dumps({
        'declared_runs':len(runs),'completed_runs':len(observed),
        'failed_or_missing_runs':[key for key,value in runs.items() if value['error']],
        'figure_generated':bool(observed),'missing_distributions_fabricated':False,
        'table_filter':'Upstream strict mean +/- 2 population standard deviations',
        'figure_data':'Raw differences retained for visibility of excluded values'
    },indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
