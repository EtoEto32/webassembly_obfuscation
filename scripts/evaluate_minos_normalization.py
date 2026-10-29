"""Frozen, offline image inference on saved comparisons; no Wasm execution.

Predicted MALIGN is the model's output, not proof of unauthorized mining.
Training overlap is unresolved; no population precision/recall claims.
"""
import hashlib
import json
import time
from minos_static_inference import ROOT, OUT, model, predict, tf


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = json.loads((OUT/'inference-adapter-checks.json').read_text(encoding='utf-8'))
    assert checks['passed'] and checks['adapter_sha256'] == digest(ROOT/'scripts/minos_static_inference.py')
    assert checks['model_sha256'] == digest(OUT/'wasm-obf-original23.h5')
    selection = []
    for group, filename in [('local-normalization', 'static-comparison.json'), ('transfer', 'comparison.json'), ('seeded-normalization', 'comparison.json')]:
        rows = json.loads((ROOT/'results/countermeasures'/group/filename).read_text(encoding='utf-8'))['records']
        for row in rows:
            path = ROOT/row['path']
            assert digest(path) == row['sha256']
            selection.append(dict(group=group, source=row['source'], variant=row['variant'], path=row['path'], sha256=row['sha256']))
    manifest = dict(selection=selection, adapter_sha256=checks['adapter_sha256'], model_sha256=checks['model_sha256'],
                    decision='argmax over MALIGN,BENIGN; ties MALIGN', preprocessing='reviewed get_pixels path, raw 0..255, Pillow default L-mode resize',
                    training_evaluation_overlap='unknown; must not claim independent detector accuracy', target_wasm_executed=False)
    # Write the complete selection and configuration before seeing scores.
    (OUT/'evaluation-selection.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    net = model()
    records = []
    for row in selection:
        start = time.perf_counter()
        result = predict(net, (ROOT/row['path']).read_bytes())
        records.append(dict(**row, **result, elapsed_ms=(time.perf_counter()-start)*1000))
    transitions = []
    for row in records:
        original = next(x for x in records if x['group'] == row['group'] and x['source'] == row['source'] and x['variant'] == 'unmodified')
        transitions.append(dict(group=row['group'], source=row['source'], variant=row['variant'],
                                original_class=original['predicted_class'], processed_class=row['predicted_class'],
                                class_changed=original['predicted_class'] != row['predicted_class'],
                                logit_margin_delta=row['malign_minus_benign_logit']-original['malign_minus_benign_logit'],
                                malign_score_delta=row['probabilities']['MALIGN']-original['probabilities']['MALIGN']))
    summary = dict(conditions=len(records), malign_predictions=sum(r['predicted_class'] == 'MALIGN' for r in records),
                   dedicated_conditions=sum(r['variant'] in ('nop', 'integer-fold', 'both') for r in records),
                   dedicated_class_changes=sum(r['class_changed'] and r['variant'] in ('nop', 'integer-fold', 'both') for r in transitions))
    report = dict(records=records, transitions=transitions, summary=summary,
                  selection_sha256=digest(OUT/'evaluation-selection.json'), evaluator_sha256=digest(ROOT/'scripts/evaluate_minos_normalization.py'),
                  tensorflow=tf.__version__, target_wasm_executed=False, model_inference_executed=True,
                  scope='Within-model scores and label transitions on selected related artifacts. Adapted explicit architecture with fixed public weights and reviewed preprocessing. Not historical environment reproduction, in-the-wild malignancy, independent precision/recall, or hash throughput. Single elapsed measurements include file read/preprocessing/inference; not latency benchmark.')
    (OUT/'normalization-inference.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
