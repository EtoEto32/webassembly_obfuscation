"""Audit all acquired SWAMPED mining seeds without executing modules or guessing labels."""
import collections
import csv
import hashlib
import json
from pathlib import Path
from analyze_corpus import acquired_rows
csv.field_size_limit(64 * 1024 * 1024)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/runtime-mining/cross-dataset/swamped'
OUT.mkdir(parents=True, exist_ok=True)
acquired = [json.loads(line) for line in (ROOT/'data/catalog/swamped/acquisition.jsonl').read_text().splitlines()]
seeds = [row for row in acquired if 'Cryptojackers_43/' in row['path'] and row.get('acquisition_status') == 'stored_verified']
with (ROOT/'results/runtime-mining/cross-dataset/mining-candidates.csv').open(encoding='utf-8') as f:
    prior = list(csv.DictReader(f))
all_acquired = acquired_rows()
records = []
for row in seeds:
    data = (ROOT/row['object']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == row['sha256']
    cache = json.loads((ROOT/'data/analysis-v2'/ (row['sha256']+'.json')).read_text())
    exports = cache['exports']; imports = cache['imports']
    exact = [dict(dataset=r['dataset'], path=r['path']) for r in all_acquired
             if r['dataset'] != 'swamped' and r['sha256'] == row['sha256']]
    core = [dict(dataset=r['dataset'], path=r['path'], sha256=r['sha256']) for r in prior
            if r['dataset'] != 'swamped' and r['core_bytes_sha256'] == cache['core_bytes_sha256']
            and r['sha256'] != row['sha256']]
    records.append(dict(path=row['path'], sha256=row['sha256'], commit=row['commit'], object=row['object'],
                        bytes=cache['bytes'], instructions=cache['instruction_count'],
                        exports=exports, imports=imports,
                        exact_cross_dataset_matches=exact, core_cross_dataset_matches=core,
                        role='public input seed; not a newly generated SWAMPED variant',
                        correctness='This interface audit does not execute modules; consult the separate runtime reports for measured subsets.',
                        obfuscation_mechanism='unconfirmed; dataset malware label is not a technique label'))
summary = dict(acquired_seeds=len(records), unique_sha256=len({r['sha256'] for r in records}),
               named_hash_exports=sum(any('hash' in e['name'].lower() for e in r['exports']) for r in records),
               exact_overlap_seeds=sum(bool(r['exact_cross_dataset_matches']) for r in records),
               core_overlap_seeds=sum(bool(r['core_cross_dataset_matches']) for r in records),
               exact_overlap_scope='All saved acquisition records; not only named mining candidates.',
               core_overlap_scope='Only existing mining-candidates.csv with cached core hashes; nonidentical-byte matches only.',
               import_names=collections.Counter(i['module']+'.'+i['name'] for r in records for i in r['imports']),
               limits=['Interface compatibility does not establish algorithm or correctness.',
                       'Static instruction totals are read from complete analyzer JSON, not truncated headers.',
                       'Published seeds and researcher-generated perturbed artifacts must be distinguished.'])
(OUT/'seed-interfaces.json').write_text(json.dumps(dict(summary=summary, modules=records), indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k != 'import_names'}, indent=2))
for r in records:
    print(r['sha256'][:12], ';'.join(e['name'] for e in r['exports'] if 'hash' in e['name'].lower()),
          'imports',len(r['imports']), 'overlap',len(r['exact_cross_dataset_matches']), len(r['core_cross_dataset_matches']))
