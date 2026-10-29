"""Summarize RQ3 collector output. Does not invent pool acceptance."""
import argparse
import csv
import json
import statistics
from pathlib import Path


def summarize(run):
    values = [int(x) for x in (run / 'reference.logs.txt').read_text().split(',')]
    if len(values) != 991:
        raise ValueError('Expected 991 retained cumulative counts from upstream collector')
    rates = [b - a for a, b in zip(values, values[1:])]
    if min(rates) < 0:
        raise ValueError('Counter reset detected')
    mean = statistics.mean(rates)
    deviation = statistics.pstdev(rates)
    # Same open interval as upstream get_table.v2.py; retain raw observations.
    filtered = [rate for rate in rates if mean - 2 * deviation < rate < mean + 2 * deviation]
    share_file = run / 'shares.jsonl'
    shares = [json.loads(line) for line in share_file.read_text().splitlines() if line] if share_file.exists() else []
    submitted = sum(s.get('event') == 'submitted' for s in shares)
    accepted = sum(s.get('event') == 'accepted' for s in shares)
    rejected = sum(s.get('event') == 'rejected' for s in shares)
    return dict(run=str(run), rates=rates, retained_samples=len(values), rate_samples=len(rates),
                mean_hps=statistics.mean(rates), median_hps=statistics.median(rates),
                reference_filtered_rates=filtered,
                reference_filtered_samples=len(filtered),
                reference_excluded_samples=len(rates)-len(filtered),
                reference_filtered_median_hps=statistics.median(filtered) if filtered else None,
                reference_filter='strict mean +/- 2 population standard deviations; upstream get_table.v2.py',
                submitted=submitted, accepted=accepted, rejected=rejected,
                hashes_computed_in_retained_intervals=sum(rates),
                hash_computation_observed=any(rate > 0 for rate in rates),
                pool_log_available=share_file.exists(),
                pool_correctness='accepted shares observed' if accepted else 'not established')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, required=True)
    args = p.parse_args()
    summary = summarize(args.run)
    rates = summary.pop('rates')
    filtered = summary.pop('reference_filtered_rates')
    with (args.run / 'hash-rates.csv').open('w', newline='', encoding='utf-8') as h:
        w = csv.writer(h)
        w.writerow(['retained_interval', 'nominal_hashes_per_second'])
        w.writerows(enumerate(rates))
    with (args.run / 'reference-filtered-rates.csv').open('w', newline='', encoding='utf-8') as h:
        w = csv.writer(h)
        w.writerow(['filtered_sample', 'nominal_hashes_per_second'])
        w.writerows(enumerate(filtered))
    (args.run / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
