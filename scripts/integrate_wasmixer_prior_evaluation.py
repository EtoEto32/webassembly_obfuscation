"""Record a primary-paper evaluation gap and connect it to saved overlap evidence."""
import csv
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/runtime-mining/cross-dataset'
OUT = BASE / 'prior-work'
source = 'https://arxiv.org/html/2308.03123v1'
evidence = 'Sections 5.2/5.5 and Table 2: mining dataset D3 is explicitly excluded from runtime overhead evaluation owing to browser/JS dependencies. Section 5.3 checks outputs for D1/D2; Section 5.4.2 evaluates D3 detection.'
role = 'Complete valid hashing of a reused input plus SWAMPED-generated controls; not a runtime evaluation of WASMixer obfuscation methods or a worldwide-first claim.'
overlap = json.loads((BASE / 'measured-corpus-overlap.json').read_text())
seed = next(r for r in overlap['modules'] if r['sha256'].startswith('046dc081'))
occurrence = next(r for r in seed['exact_acquired_occurrences'] if r['dataset'] == 'wasmixer')
assert occurrence['path'] == 'benchmark/mining_programs/2.wasm'
review = dict(source=source, version='arXiv:2308.03123v1', review_date='2026-10-08',
              evidence=evidence, scope='Reviewed primary manuscript; not all subsequent papers, supplements, or unpublished executions.',
              overlap=dict(sha256=seed['sha256'], occurrence=occurrence,
                           evidence='../measured-corpus-overlap.json',
                           table4_id_candidate=seed['sha256'][-8:],
                           table4_id_limitation='The matching eight-character ID is consistent with Table 4 but is not used alone as a full binary identity proof.'),
              current_role=role,
              limitations=['An input reappearing in a different corpus is not a new independent binary.',
                           'The current generated pair uses SWAMPED nop/constant splitting, not WASMixer transformations.',
                           'Reported exclusion in this version does not establish absence of every earlier or later hash-rate evaluation.'])
(OUT / 'wasmixer-primary-review.json').write_text(json.dumps(review, indent=2)+'\n')
path = OUT / 'evaluation-coverage.json'
coverage = json.loads(path.read_text())
coverage['reviewed_sources'] = [r for r in coverage['reviewed_sources'] if r['name'] != 'WASMixer']
coverage['reviewed_sources'].append(dict(name='WASMixer', source=source, hash_rate_evaluated=False,
    execution_time_evaluated=True, hash_rate_scope='Mining D3 explicitly excluded in reviewed manuscript.',
    evidence=evidence, current_role=role))
coverage['novelty_audit']['date_jst'] = '2026-10-08'
coverage['novelty_audit']['requirements'][0] = 'Trace exact binary reuse and prior benchmark coverage; reused input can support a new condition/method comparison but not a new-binary claim.'
path.write_text(json.dumps(coverage, indent=2)+'\n')
path = OUT / 'evaluation-comparison.csv'
with path.open(encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = [r for r in reader if r['study'] != 'WASMixer']
rows.append(dict(study='WASMixer', primary_source=source, reported_hash_rate=False,
                 reported_execution_time=True, evidence=evidence, evaluation_role=role))
with path.open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
print('WASMixer primary-paper mining exclusion recorded; seven source comparisons, with reused-input and method scope explicit.')
