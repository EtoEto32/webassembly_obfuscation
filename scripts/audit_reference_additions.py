"""Check new author reference samples against the frozen sensitivity inputs.

Exact-byte overlap establishes shared artifacts, not semantic parentage or the
maliciousness of a deployment. Crawled-archive previews are never counted here.
"""
import collections
import datetime
import hashlib
import json
from analyze_corpus import ROOT, acquired_rows


def main():
    rows=[r for r in acquired_rows() if r['dataset']!='wasm-obf-controls']
    by_dataset=collections.defaultdict(set)
    for row in rows:
        by_dataset[row['dataset']].add(row['sha256'])
    labels={r['sha256']:r['path'].split('/')[0] for r in rows
            if r['dataset']=='wasmmal' and r['path'].startswith(('malware/','benign/'))}
    prior_references={r['sha256'] for r in rows if r['dataset']=='wasmbench' or
                      (r['dataset']=='swamped' and r['path'].startswith('experimental_data/'))}
    old_anchors={s for s in prior_references if labels.get(s)=='malware'}
    sensitivity_path=ROOT/'results/sensitivity/summary.json'
    sensitivity=json.loads(sensitivity_path.read_text(encoding='utf-8'))
    if len(old_anchors)!=sensitivity['reference_hashes']:
        raise ValueError('Existing sensitivity reference scope changed; inspect before comparing')
    samples=[r for r in rows if r['dataset']=='minesweeper' and not r.get('artifact')]
    sample_hashes={r['sha256'] for r in samples}
    details=[]
    for row in sorted(samples,key=lambda r:r['path']):
        sha=row['sha256']
        details.append({'sha256':sha,'path':row['path'],
                        'author_directory':row['path'].split('/')[-2],
                        'acquisition_status':row['acquisition_status'],
                        'wasmmal_author_label':labels.get(sha,'absent'),
                        'already_in_sensitivity_reference':sha in old_anchors,
                        'datasets_with_identical_bytes':sorted(d for d,s in by_dataset.items() if sha in s)})
    expanded_anchors=old_anchors | {s for s in sample_hashes if labels.get(s)=='malware'}
    additions=[]
    for dataset in ('minesweeper','wasm-r3'):
        other=set().union(*(s for d,s in by_dataset.items() if d!=dataset))
        additions.append({'dataset':dataset,'unique_sha256':len(by_dataset[dataset]),
                          'shared_with_any_other_dataset':len(by_dataset[dataset]&other),
                          'exclusive_sha256':len(by_dataset[dataset]-other),
                          'pairwise_overlap':{d:len(by_dataset[dataset]&s)
                                              for d,s in sorted(by_dataset.items()) if d!=dataset}})
    report={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'scope':'Pinned MineSweeper repository samples and complete OOPSLA_2024 Wasm-R3 benchmarks; external crawled archive handled separately',
            'new_dataset_overlap':additions,
            'minesweeper_repository':{'occurrences':len(samples),'unique_sha256':len(sample_hashes),
                'wasmmal_author_label_counts':dict(collections.Counter(labels.get(s,'absent') for s in sample_hashes)),
                'author_directory_counts':dict(collections.Counter(r['author_directory'] for r in details)),
                'acquisition_status_counts':dict(collections.Counter(r['acquisition_status'] for r in samples))},
            'sensitivity_reference_check':{'old_anchors':len(old_anchors),'expanded_anchors':len(expanded_anchors),
                'additional_anchor_hashes':sorted(expanded_anchors-old_anchors),
                'anchor_set_unchanged':expanded_anchors==old_anchors,
                'existing_summary_sha256':hashlib.sha256(sensitivity_path.read_bytes()).hexdigest()},
            'input_manifests':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                               for p in sorted((ROOT/'data/catalog').glob('*/acquisition.jsonl'))],
            'interpretation':'Shared bytes preserve all source memberships; this does not independently validate WasmMal labels, family membership, or parentage.'}
    output=ROOT/'results/provenance';output.mkdir(parents=True,exist_ok=True)
    (output/'reference-additions.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (output/'minesweeper-repository-members.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in details),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='input_manifests'}),flush=True)


if __name__=='__main__':main()
