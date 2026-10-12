"""Predefined raw vs encode-scale comparison. No tuning, retraining or Wasm run."""
import hashlib
import json
import numpy as np
from minos_static_inference import ROOT, OUT, model, pixels, tf, CLASSES


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = json.loads((OUT/'normalization-inference.json').read_text(encoding='utf-8'))
    selection = json.loads((OUT/'evaluation-selection.json').read_text(encoding='utf-8'))
    assert sha(ROOT/'scripts/minos_static_inference.py') == selection['adapter_sha256']
    manifest = dict(selection_sha256=sha(OUT/'evaluation-selection.json'),
                    scales=[dict(name='get_pixels', divisor=1), dict(name='encode', divisor=255)],
                    class_order=list(CLASSES), decision='argmax; ties MALIGN',
                    rationale='Published get_pixels returns uint8; data_set_builder uses encode which divides resized pixels by255. The saved model training path is not established by source availability.',
                    threshold_tuned=False, retrained=False)
    (OUT/'scale-sensitivity-selection.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    net = model()
    features = tf.keras.Model(net.inputs[0], net.layers[-2].output)
    dense = net.layers[-1]
    records = []
    for row in original['records']:
        path = ROOT/row['path']
        assert sha(path) == row['sha256']
        x = pixels(path.read_bytes())/np.float32(255)
        scores = net(x, training=False).numpy()[0]
        hidden = features(x, training=False)
        logits = (tf.linalg.matmul(hidden, dense.kernel)+dense.bias).numpy()[0]
        assert np.isfinite(scores).all() and np.isfinite(logits).all()
        records.append(dict(group=row['group'], source=row['source'], variant=row['variant'], sha256=row['sha256'],
                            probabilities=dict(zip(CLASSES, map(float, scores))), logits=dict(zip(CLASSES, map(float, logits))),
                            predicted_class=CLASSES[int(np.argmax(scores))], raw_predicted_class=row['predicted_class'],
                            class_differs_between_scales=CLASSES[int(np.argmax(scores))] != row['predicted_class']))
    transitions = []
    for row in records:
        baseline = next(x for x in records if x['group'] == row['group'] and x['source'] == row['source'] and x['variant'] == 'unmodified')
        transitions.append(dict(group=row['group'], source=row['source'], variant=row['variant'],
                                original_class=baseline['predicted_class'], processed_class=row['predicted_class'],
                                class_changed=baseline['predicted_class'] != row['predicted_class']))
    summary = dict(conditions=len(records), normalized_malign_predictions=sum(x['predicted_class'] == 'MALIGN' for x in records),
                   scale_class_changes=sum(x['class_differs_between_scales'] for x in records),
                   dedicated_normalized_class_changes=sum(x['class_changed'] and x['variant'] in ('nop', 'integer-fold', 'both') for x in transitions))
    report = dict(summary=summary, records=records, transitions=transitions,
                  original_inference_sha256=sha(OUT/'normalization-inference.json'),
                  selection_sha256=sha(OUT/'scale-sensitivity-selection.json'),
                  model_sha256=selection['model_sha256'], evaluator_sha256=sha(ROOT/'scripts/evaluate_minos_scale_sensitivity.py'),
                  target_wasm_executed=False, trained_model_provenance_unresolved=True,
                  scope='Source-grounded preprocessing sensitivity for a fixed model and corpus. Not an accuracy benchmark or selection of the most favorable preprocessing.')
    (OUT/'scale-sensitivity.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
