"""Index existing evidence and verify recorded runtime dependencies, without execution."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/runtime-mining/cross-dataset'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(65536),b''):h.update(chunk)
    return h.hexdigest()
runtime=[('proof-of-theft/xmr-repeated-throughput-20261008.json',[
    ('script_sha256','experiments/runtime-reference/proof-xmr-benchmark.cjs'),
    ('host_loader_sha256','experiments/runtime-reference/proof-glue-controls.cjs'),
    ('manifest_sha256','results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json')]),
    ('swamped/controlled-pair-repeated-throughput.json',[
    ('script_sha256','experiments/runtime-reference/swamped-pair-benchmark.cjs'),
    ('host_sha256','experiments/runtime-reference/swamped-host.cjs'),
    ('manifest_sha256','results/runtime-mining/cross-dataset/swamped/controlled-pair-manifest.json'),
    ('vector_manifest_sha256','results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json')])]
dependency_checks=[]
for report_name,deps in runtime:
    report=json.loads((BASE/report_name).read_text())
    for key,name in deps:
        actual=sha(ROOT/name)
        dependency_checks.append(dict(report=report_name,file=name,expected_sha256=report[key],
                                       actual_sha256=actual,matches=actual==report[key]))
files=['selected-hash-evaluation-status.json','selected-hash-evaluation-status.csv',
 'goal-requirements-audit.json','goal-requirements-audit.txt',
 'mechanism-claim-scope-review.json',
 'hash-structure-comparison.json','hash-structure-comparison.csv','hash-structure-comparison.pdf',
 'rq1-rq2-runtime-evidence.csv','rq1-rq2-runtime-evidence.json','runtime-number-audit.json',
 'rq1-presentation-review.json',
 'repetition-order-review.json','repetition-order-review.csv','repetition-order-review.pdf',
 'measured-corpus-overlap.json','swamped/seed-interfaces.json',
 'prior-work/evaluation-comparison.csv','prior-work/evaluation-coverage.json',
 'prior-work/minerray-primary-review.json',
 'prior-work/emcc-obf-toolchain-review.json',
 'prior-work/wasmixer-primary-review.json',
 'proof-of-theft/glue-control-input.json','proof-of-theft/runtime-mechanism-audit.json',
 'proof-of-theft/original-glue-public-vector-check-corrected-20261008.json',
 'proof-of-theft/hash-throughput-preliminary-20261007-retry.json',
 'proof-of-theft/preliminary-summary.csv','proof-of-theft/preliminary-throughput.pdf',
 'proof-of-theft/xmr-repeated-throughput-20261008.json','proof-of-theft/xmr-repeated-summary.json',
 'proof-of-theft/xmr-repeated-throughput.pdf','proof-of-theft/xmr-source-correspondence.json',
 'proof-of-theft/xmr-function-scope-audit.json','proof-of-theft/xmr-core-substitution-review.json',
 'proof-of-theft/xmr-helper-flattening-review.json','proof-of-theft/xmr-helper-path-review.json',
 'proof-of-theft/xmr-split-wrapper-review.json',
 'proof-of-theft/xmr-split-helper-review.json',
 'proof-of-theft/source-reuse-review.json',
 'proof-of-theft/xmr-cleanup-flattening-review.json',
 'proof-of-theft/xmr-initialization-flattening-review.json',
 'proof-of-theft/xmr-key-import-flattening-review.json',
 'proof-of-theft/xmr-f113-dispatch-entry-review.json',
 'proof-of-theft/xmr-f113-variant-guard-review.json',
 'proof-of-theft/xmr-normal-interpreter-review.json',
 'proof-of-theft/xmr-v0-core-scope-review.json',
 'proof-of-theft/cryptonight-entrypoint-review.json',
 'proof-of-theft/cryptonight-hash-abi-review.json',
 'proof-of-theft/cryptonight-final-table-review.json',
 'proof-of-theft/cryptonight-core-flattening-review.json',
 'proof-of-theft/cryptonight-source-reuse-review.json',
 'proof-of-theft/cryptonight-export-only-manifest.json',
 'proof-of-theft/cryptonight-runner-preparation.json',
 'proof-of-theft/cryptonight-repetition-plan.json',
 'proof-of-theft/cryptonight-repetition-log-review.json',
 'swamped/controlled-pair-manifest.json','swamped/controlled-pair-mechanism-audit.json',
 'swamped/controlled-pair-public-vector-check.json','swamped/controlled-pair-repeated-throughput.json',
 'swamped/controlled-pair-summary.json','swamped/controlled-pair-throughput.pdf']
records=[]
for name in files:
    p=BASE/name
    assert p.is_file() and p.stat().st_size>0,name
    records.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
for name in ['results/rq-validation/refreshed-rq1-controls-audit.json','results/rq-validation/review-ledger.json',
             'results/mining-methods/paper-audit.json','results/mining-methods/paper-claim-evidence.json',
             'paper/main.tex','paper/references.bib','paper/README.md','paper/terminology-review.md',
             'experiments/runtime-reference/csec-submission-draft.txt']:
    p=ROOT/name;assert p.is_file()
    records.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
index=dict(files=records,recorded_runtime_dependencies=dependency_checks,
           scope='Index of current selected evidence; hashes verify integrity, not scientific correctness or completion.',
           unresolved=['University permission for new executions pending.',
                       'Full transformation scope and dynamic path coverage incomplete.',
                       'Independent implementation ancestry incomplete.',
                       'Controlled historical rebuilds of distributed variants incomplete.',
                       'Built-in LaTeX compiler unavailable; final PDF and 6-8 pages unverified.'])
(BASE/'current-evidence-index.json').write_text(json.dumps(index,indent=2)+'\n')
assert all(x['matches'] for x in dependency_checks),'Recorded runtime dependencies have changed; inspect index before replay.'
print(f'{len(records)} existing evidence files indexed; all {len(dependency_checks)} recorded runtime dependencies match.')
