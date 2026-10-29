"""Compare measured module identities against saved acquisition and candidate records."""
import collections
import csv
import json
from pathlib import Path
from analyze_corpus import acquired_rows
from inventory_cross_dataset_runtime import interface_metadata
csv.field_size_limit(64 * 1024 * 1024)
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/runtime-mining/cross-dataset'
measured=json.loads((BASE/'rq1-rq2-runtime-evidence.json').read_text())['modules']
acquired=acquired_rows()
by_sha=collections.defaultdict(list)
for r in acquired:
    if r.get('sha256'):
        by_sha[r['sha256']].append({k:r.get(k) for k in ('dataset','path','acquisition_status')})
with (BASE/'mining-candidates.csv').open(encoding='utf-8-sig',newline='') as f:
    candidates=list(csv.DictReader(f))
by_core=collections.defaultdict(list)
for r in candidates:
    if r.get('core_bytes_sha256'):
        by_core[r['core_bytes_sha256']].append({k:r[k] for k in ('dataset','path','sha256')})
rows=[]
for r in measured:
    metadata=ROOT/'data/analysis-v2'/f"{r['sha256']}.json"
    core=interface_metadata(metadata).get('core_bytes_sha256') if metadata.exists() else None
    if core is None and r['dataset'].startswith('SWAMPED'):
        p=BASE/'swamped'/f"{r['name']}-static.json"
        core=json.loads(p.read_text()).get('core_bytes_sha256')
    occurrences=by_sha.get(r['sha256'],[])
    core_occurrences=by_core.get(core,[]) if core else []
    rows.append(dict(name=r['name'],sha256=r['sha256'],core_bytes_sha256=core,
                     exact_acquired_occurrences=occurrences,
                     exact_datasets=sorted({x['dataset'] for x in occurrences}),
                     core_candidate_occurrences=core_occurrences,
                     core_candidate_datasets=sorted({x['dataset'] for x in core_occurrences}),
                     mechanism_evidence=r['mechanism_evidence']))
report=dict(exact_scope='All saved acquisition records returned by acquired_rows; failed/unhashed acquisitions cannot be compared.',
            acquisition_rows=len(acquired),acquisition_unique_sha256=len(by_sha),
            core_scope='Existing mining-candidates.csv entries with cached core digest; not the entire acquisition corpus.',
            candidate_rows=len(candidates),candidate_rows_with_core=sum(bool(r.get('core_bytes_sha256')) for r in candidates),
            modules=rows,
            limitations=['Different binary/core hashes do not establish independent source ancestry.',
                         'A reused binary in another corpus is not proof that its hashing performance was published.',
                         'No exact match in acquired records is not proof of a world-first evaluation.',
                         'Core digest excludes custom sections but retains other binary encoding differences.'])
(BASE/'measured-corpus-overlap.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(acquired_rows=len(acquired),candidate_rows=len(candidates),
    modules=[{k:r[k] for k in ('name','exact_datasets','core_candidate_datasets')} for r in rows]),indent=2))
