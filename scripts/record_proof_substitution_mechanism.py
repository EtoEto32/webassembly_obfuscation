"""Record manually reviewed algebra, including paths excluded by the benchmark."""
import hashlib
import json
from pathlib import Path
from audit_proof_runtime_mechanisms import function_excerpt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset/proof-of-theft'
original, _ = function_excerpt(OUT/'xmr-original.wat', 'hash')
modified, first = function_excerpt(OUT/'xmr-substitution.wat', 'hash')
assert 'i32.const 1368051000' not in original
assert modified.count('i32.const 1368051000') == 2
assert 'local.get $l47\n        local.get $l48\n        i32.sub' in modified
assert 'local.get $l49\n        local.get $l50\n        i32.add' in modified
assert 'local.get $l69\n        local.get $l70\n        i32.sub' in modified
assert 'local.get $l68\n        local.get $l71\n        i32.sub' in modified
mask = (1 << 32)-1
assert all(((x-1368051000-6+1368051000)&mask) == ((x-6)&mask) for x in range(256))
record = dict(sha256='eb15e17a985fe1d192296d5084b0fdac220a9e8f16a406eb54167d54190b6b90',
              function='hash', wat_first_line=first,
              excerpt='xmr-hash-substitution-excerpt.wat.txt',
              excerpt_sha256=hashlib.sha256((modified+'\n').encode()).hexdigest(),
              source_diff='xmr-hash-substitution-local-normalized.diff.txt',
              equations=[dict(original='x - 6', replacement='(x - 1368051000) - 6 + 1368051000',
                              input='unsigned first input byte', domain='i32 modular arithmetic',
                              path='variant selection when first byte >= 7',
                              executed_in_cn0_benchmark=False),
                         dict(original='nonce + 1', replacement='nonce - (0 - 1)',
                              input='32-bit nonce', domain='i32 modular arithmetic',
                              path='after hash failed target comparison',
                              executed_in_cn0_benchmark=False)],
              finite_arithmetic_checks=256,
              scope='Two replacement expressions in exported hash wrapper; not all hash-core functions',
              benchmark_relation='Both reviewed replacements are on paths not exercised by the maximum-target CN/0 benchmark. They cannot explain its whole slowdown.',
              conclusion='Arithmetic substitution verified locally by counterpart tracing and modular identities, not inferred from operator counts.')
path = OUT/'runtime-mechanism-audit.json'
audit = json.loads(path.read_text())
audit['reviewed_substitution'] = record
for row in audit['modules']:
    if row['sha256'] == record['sha256']:
        row['mechanism_status'] = 'two arithmetic substitutions confirmed in exported hash wrapper; reviewed paths excluded by benchmark'
        row['mechanism_evidence'] = 'runtime-mechanism-audit.json:reviewed_substitution'
path.write_text(json.dumps(audit, indent=2)+'\n')
print('Recorded two equivalent arithmetic replacements and their unmeasured paths')
