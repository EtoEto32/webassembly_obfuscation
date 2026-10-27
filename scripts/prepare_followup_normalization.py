"""Freeze post-performance normalization comparisons; never instantiate Wasm."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target=OUT/'normalization-plan.json';assert not target.exists()
    performance=OUT/'confirmatory-summary.json';summary=json.loads(performance.read_text(encoding='utf-8'))
    assert summary['status']=='all-three-sessions-audited' and summary['timed_blocks']==272
    for source in summary['sources']:
        run=ROOT/source['run'];assert sha(run/'outputs/runtime.json')==source['measurement_sha256']
        assert sha(run/'confirmatory-audit.json')==source['audit_sha256']
    calls=OUT/'callsite-summary.json';assert json.loads(calls.read_text(encoding='utf-8'))['status']=='audited-site-sums-match-helper-entry-counts'
    generation=json.loads((OUT/'controlled-generation-v2.json').read_text(encoding='utf-8'))
    inputs=[dict(id=r['id'],family=r['family'],transformation=r['method'],path=r['path'],sha256=r['sha256'],
        truth='reference' if r['method']=='baseline' else 'index-preserving-generated-control') for r in generation['cases']]
    spec=json.loads((ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/glue-control-input.json').read_text(encoding='utf-8'))
    for label,method in [('published-flat','xmr-wasm-emccobf-flattening'),('published-sub','xmr-wasm-emccobf-substitution')]:
        r=next(x for x in spec['modules'] if x['method']==method)
        inputs.append(dict(id=label,family='xmr-wasm',transformation=method,path=r['object'],sha256=r['sha256'],
            truth='reviewed-helper-pairs-only',reviewed_function_indices=[112,118]))
    assert len(inputs)==11
    for r in inputs:assert sha(ROOT/r['path'])==r['sha256']
    features=['--enable-reference-types','--enable-multivalue','--enable-simd']
    methods=[dict(id='unmodified',kind='copy'),dict(id='nop',kind='local',rules=['nop']),
        dict(id='integer-fold',kind='local',rules=['integer-fold']),dict(id='both',kind='local',rules=['nop','integer-fold']),
        dict(id='binaryen-local',kind='binaryen',flags=['--vacuum','--precompute',*features]),
        dict(id='binaryen-O2',kind='binaryen',flags=['-O2',*features]),dict(id='binaryen-O3',kind='binaryen',flags=['-O3',*features])]
    paths=['scripts/normalize_wat_local.py','scripts/prepare_followup_controlled.py','scripts/analyze_corpus.py',
        'scripts/audit_normalization_signatures.py','scripts/audit_normalization_resources.py',
        'docs/followup-normalization-protocol-20261016.md','.tools/wabt-1.0.42/bin/wasm2wat.exe',
        '.tools/wabt-1.0.42/bin/wat2wasm.exe','.tools/wabt-1.0.42/bin/wasm-validate.exe','.tools/binaryen-version_133/bin/wasm-opt.exe']
    plan=dict(created_utc=datetime.now(timezone.utc).isoformat(),frozen_before_execution=True,
        inputs=inputs,methods=methods,labels=77,batches={'swamped':21,'xmr-wasm':35,'webminerpoolhashcn':21},
        required_sources=[dict(path=p,sha256=sha(ROOT/p)) for p in paths],
        performance_summary_sha256=sha(performance),callsite_summary_sha256=sha(calls),
        references=[r['id'] for r in inputs if r['truth']=='reference'],
        function_task='All defined functions of six generated controls, plus reviewed f112/f118 in two published complex modules. Track provenance with names in auxiliary copies, require identical noncustom output, remove names and function indices from features. Count removed/untrackable origins separately.',
        module_task='Eight queries per method against three equally processed references; exact canonical-WAT SHA lookup. Family and provenance are grading data only.',
        output_scope='Finite published and reference-derived 76-byte vectors in fresh/forward/reverse states; not whole-module equivalence.',
        timing_scope='Record common input presentation, processing/validation/canonicalization and lookup time separately. Descriptive only; no new throughput claims.',
        prior_method_scope='Binaryen133 O3 follows the published option but is not historical-commit reproduction.',
        runtime_executed=False,normalizer_rules_changed=False)
    target.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(plan=str(target),sha256=sha(target),inputs=len(inputs),labels=77)))


if __name__=='__main__':main()
