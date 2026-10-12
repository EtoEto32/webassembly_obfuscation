"""Join existing runtime results to reviewed mechanisms by binary SHA-256."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/runtime-mining/cross-dataset'
P = BASE/'proof-of-theft'
S = BASE/'swamped'
audit = json.loads((P/'runtime-mechanism-audit.json').read_text())
by_sha = {r['sha256']: r for r in audit['modules']}
public_checks = {r['sha256']: r for r in json.loads((P/'original-glue-public-vector-check-corrected-20261008.json').read_text())['results']}
rows = []
with (P/'preliminary-summary.csv').open(encoding='utf-8-sig',newline='') as f:
    wmp = list(csv.DictReader(f))
xmr = json.loads((P/'xmr-repeated-summary.json').read_text())
swamp = json.loads((S/'controlled-pair-summary.json').read_text())
cases = {r['sha256']: r for r in json.loads((S/'controlled-pair-manifest.json').read_text())['cases']}
for r in wmp+xmr:
    a = by_sha[r['sha256']]
    assert not a['wasabi_hook_imports']
    family = a['family']
    check = public_checks[r['sha256']]
    assert check['status']=='all applicable public vectors matched'
    assert all(v['actual']==v['expected'] for v in check['outputs'])
    name = r['method']
    reference = next(x['sha256'] for x in wmp+xmr if x['method']==family)
    if family=='webminerpoolhashcn':
        mechanism='Unconfirmed; all five distributed Makefiles specify -enable-bcfobf.'
        scope='No independent mechanism label established.'
        evidence='proof-of-theft/runtime-mechanism-audit.json'
        vectors=5
        flags=';'.join(a['build_flags'])
    elif name.endswith('flattening'):
        mechanism='State dispatcher in exported hash wrapper, XOR helpers f112/f118, key import f82, initialization f83 and cleanup f86; no br_table required.'
        scope='hash wrapper and helpers f82/f83/f86/f112/f118 reviewed; f113 entry only, not full graph. f113 caller requires variant>=4; measured v0 inputs select0. f111 net text growth9428 occurs inside variant>=4 block; retained3609 lines/local types match after local/label renaming. Helper changes, expanded local declarations, JIT and module state remain outside this equivalence scope; dynamic coverage/frequency unmeasured.'
        evidence='proof-of-theft/xmr-hash-flattening-reviewed.wat.txt;proof-of-theft/xmr-helper-flattening-review.json;proof-of-theft/xmr-helper-path-review.json;proof-of-theft/xmr-cleanup-flattening-review.json;proof-of-theft/xmr-initialization-flattening-review.json;proof-of-theft/xmr-key-import-flattening-review.json;proof-of-theft/xmr-f113-dispatch-entry-review.json;proof-of-theft/xmr-f113-variant-guard-review.json;proof-of-theft/xmr-normal-interpreter-review.json;proof-of-theft/xmr-v0-core-scope-review.json'
        vectors=3
        flags=';'.join(a['build_flags'])
    elif name.endswith('substitution'):
        mechanism='Equivalent variant/nonce expressions in hash; equivalent x<<4 address expression in f111.'
        scope='hash wrapper and one f111 nested-loop expression; dynamic path coverage not measured.'
        evidence='proof-of-theft/xmr-core-substitution-review.json'
        vectors=3
        flags=';'.join(a['build_flags'])
    elif name.endswith('split'):
        mechanism='Changed scratch/frame layout in f35/f112/f118 and structured branch nesting in XOR helpers; declared splitting mechanism remains unconfirmed.'
        scope='f35 reserves 48 bytes in three updates versus 32 and forwards the same symbolic arguments. f112/f118 retain XOR loop bounds/increment with changed scratch locations and exit-block nesting. No full equivalence or dynamic coverage claim.'
        evidence='proof-of-theft/xmr-split-wrapper-review.json;proof-of-theft/xmr-split-helper-review.json'
        vectors=3
        flags=';'.join(a['build_flags'])
    elif name==family:
        mechanism='Distributed reference; absence of all obfuscation not proven.'
        scope='Reference for same-family descriptive comparison.'
        evidence='proof-of-theft/xmr-source-correspondence.json'
        vectors=3
        flags=';'.join(a['build_flags'])
    else:
        mechanism='Declared setting only; specific mechanism not independently confirmed.'
        scope='Changed saved function text is not sufficient for a transformation label.'
        evidence='proof-of-theft/runtime-mechanism-audit.json'
        vectors=3
        flags=';'.join(a['build_flags'])
    rows.append(dict(dataset='Proof-of-Theft',name=name,sha256=r['sha256'],reference_sha256=reference,
                     provenance=a['path'],declared_flags=flags,confirmed_mechanism=mechanism,
                     reviewed_scope=scope,mechanism_evidence=evidence,wasabi_hooks=False,
                     public_vectors_matched=len(check['outputs']),public_vector_algorithm='cn/0',
                     benchmark_algorithm='cn/pico' if family=='webminerpoolhashcn' else 'cn/0',
                     benchmark_output_evidence='13 recorded accepted cn/pico outputs' if family=='webminerpoolhashcn' else 'Applicable XMRig cn/0 vectors',
                     repetitions=r['repetitions'],
                     median_hps=r['median_hps'],min_hps=r['min_hps'],max_hps=r['max_hps'],
                     instructions=r['instructions'],bytes=r['bytes'],
                     result_evidence='proof-of-theft/'+('preliminary-summary.csv' if family=='webminerpoolhashcn' else 'xmr-repeated-summary.json'),
                     interpretation='Descriptive distributed-artifact comparison; historical build conditions not controlled.'))
for r in swamp:
    c=cases[r['sha256']]
    if c['source_function']:
        mechanism='nop insertion' if 'nop' in c['source_function'] else 'Integer constant splitting with addition modulo word size'
        scope=f"{r['transformed_functions']} functions, {r['transformation_sites']} positions; changes can be reversed to the full reference WAT."
    else:
        mechanism='Reference roundtrip exactly matches original binary SHA-256.'
        scope='Input seed; not labeled as a proven unobfuscated real-world binary.'
    rows.append(dict(dataset='SWAMPED input plus locally generated controls',name=r['name'],sha256=r['sha256'],
                     reference_sha256=next(x['sha256'] for x in swamp if x['transformed_functions']==0),
                     provenance=c['object'],declared_flags=c['source_function'] or '',
                     confirmed_mechanism=mechanism,reviewed_scope=scope,
                     mechanism_evidence='swamped/controlled-pair-mechanism-audit.json',wasabi_hooks=False,
                     public_vectors_matched=r['correct_public_vectors'],public_vector_algorithm='cn/0',
                     benchmark_algorithm='cn/0',benchmark_output_evidence='Five XMRig cn/0 vectors',repetitions=r['repetitions'],
                     median_hps=r['median_hps'],min_hps=r['min_hps'],max_hps=r['max_hps'],
                     instructions=r['instructions'],bytes=r['bytes'],result_evidence='swamped/controlled-pair-summary.json',
                     interpretation='Same assembler and recovered host; three repetitions overlap; no claim of a definitive small performance effect.'))
assert len(rows)==13 and len({r['sha256'] for r in rows})==13
with (BASE/'rq1-rq2-runtime-evidence.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(BASE/'rq1-rq2-runtime-evidence.json').write_text(json.dumps(dict(modules=rows,
    scope='13 unique local runtime artifacts: 10 distributed Proof-of-Theft binaries, one SWAMPED input, two locally generated transformations.',
    excluded='Earlier external-pool experiments and other corpus-only static analyses are separate evidence; no new hash execution.'),indent=2)+'\n')
print(f'Joined {len(rows)} unique artifacts with explicit mechanism scope and existing runtime results.')
