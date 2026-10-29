"""Validate the shortened manuscript against saved measurements; never execute Wasm."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/mining-methods'

def main():
    tex = (ROOT / 'paper/main.tex').read_text(encoding='utf-8')
    bib = (ROOT / 'paper/references.bib').read_text(encoding='utf-8')
    keys = set(re.findall(r'@\w+\s*\{\s*([^,\s]+)', bib))
    cited = {k.strip() for group in re.findall(r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}', tex) for k in group.split(',')}
    assert not cited - keys
    labels = re.findall(r'\\label\{([^}]+)\}', tex)
    assert len(labels) == len(set(labels))
    assert not set(re.findall(r'\\(?:ref|pageref)\{([^}]+)\}', tex)) - set(labels)
    assert '\\item[RQ1]' in tex and '\\item[RQ2]' in tex
    assert '13' in tex and 'ローカル' in tex and any(term in tex for term in ('反復', '繰り返'))
    for name in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', tex):
        assert (ROOT / 'paper' / name).is_file()
    # Check the interface claims against saved, SHA-linked static evidence.
    # Type equality is not a proof of output or whole-module equivalence.
    counter = ROOT / 'results/countermeasures'
    signatures = json.loads((counter / 'interface-signature-audit.json').read_text(encoding='utf-8'))['records']
    resources = json.loads((counter / 'interface-resource-audit.json').read_text(encoding='utf-8'))['records']
    assert len(signatures) == len(resources) == 144
    custom = {'nop', 'integer-fold', 'both'}
    dedicated = [r for r in signatures if r['variant'] in custom]
    assert len(dedicated) == 72 and all(r['function_signatures_equal'] for r in dedicated)
    assert all(r['exported_function_signatures_equal'] for r in signatures)
    assert sum(not r['function_signatures_equal'] for r in signatures) == 6
    dedicated_resources = [r for r in resources if r['variant'] in custom]
    assert len(dedicated_resources) == 72
    assert all(r['imported_resources_equal'] and r['exported_resources_equal'] and r['defined_resource_types_equal'] for r in dedicated_resources)
    assert all(r['exported_resources_equal'] for r in resources)
    assert sum(not r['imported_resources_equal'] for r in resources) == 2
    key = lambda r: (r['group'], r['source'], r['variant'])
    expected = {}
    for group, filename in [('local-normalization', 'static-comparison.json'), ('transfer', 'comparison.json'), ('seeded-normalization', 'comparison.json')]:
        for row in json.loads((counter / group / filename).read_text(encoding='utf-8'))['records']:
            digest = hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest()
            assert digest == row['sha256']
            expected[(group, row['source'], row['variant'])] = digest
    for audit in (signatures, resources):
        assert len({key(r) for r in audit}) == 144
        assert {key(r): r['sha256'] for r in audit} == expected
    for phrase in ('専用72条件は署名・リソース宣言を保持', '型保持だけで意味保存は保証しない'):
        assert phrase in tex
    for filename, script in [('interface-signature-audit.json', 'audit_normalization_signatures.py'), ('interface-resource-audit.json', 'audit_normalization_resources.py')]:
        assert json.loads((counter / filename).read_text(encoding='utf-8'))['evaluator_sha256'] == hashlib.sha256((ROOT / 'scripts' / script).read_bytes()).hexdigest()
    feature_report = json.loads((counter / 'feature-loss/comparison.json').read_text(encoding='utf-8'))
    feature_rows = feature_report['records']
    assert len(feature_rows) == 144 and {key(r): r['processed_sha256'] for r in feature_rows} == expected
    selected = [r for r in feature_rows if r['variant'] in custom]
    assert len(selected) == 72
    assert sum(r['nop_presence_removed'] for r in selected) == 10
    assert sum(r['instruction_count_before'] != r['instruction_count_after'] for r in selected) == 36
    assert all(all(r['preserved_category_counts'].values()) for r in selected)
    assert feature_report['evaluator_sha256'] == hashlib.sha256((ROOT / 'scripts/analyze_normalization_feature_loss.py').read_bytes()).hexdigest()
    assert '10条件でnopの有無' in tex and '36条件で命令総数' in tex
    detector = counter / 'detector-feasibility'
    inference = json.loads((detector / 'normalization-inference.json').read_text(encoding='utf-8'))
    sensitivity = json.loads((detector / 'scale-sensitivity.json').read_text(encoding='utf-8'))
    assert len(inference['records']) == len(sensitivity['records']) == 144
    assert {key(r): r['sha256'] for r in inference['records']} == expected
    assert {key(r): r['sha256'] for r in sensitivity['records']} == expected
    assert sensitivity['summary']['scale_class_changes'] == 21
    assert inference['summary']['dedicated_class_changes'] == sensitivity['summary']['dedicated_normalized_class_changes'] == 0
    assert sensitivity['original_inference_sha256'] == hashlib.sha256((detector / 'normalization-inference.json').read_bytes()).hexdigest()
    assert sensitivity['evaluator_sha256'] == hashlib.sha256((ROOT / 'scripts/evaluate_minos_scale_sensitivity.py').read_bytes()).hexdigest()
    assert '144条件中21条件' in tex and '両尺度とも0' in tex and '訓練重複・学習尺度が未確定' in tex
    # The additional experiment is separate from the earlier three-repetition logs.
    run = counter / 'runtime-runs/execute-120f528e37424ec6806047c933011eec'
    summary = json.loads((run / 'summary.json').read_text(encoding='utf-8'))
    assert summary['measurement_sha256'] == hashlib.sha256((run / 'outputs/measurement.json').read_bytes()).hexdigest()
    assert (summary['blocks'], summary['unique_artifacts'], summary['label_conditions']) == (138, 23, 72)
    assert all(row['repetitions'] == 6 for row in summary['rows'])
    table = tex.split('\\label{tab:normalization-runtime}', 1)[1].split('\\end{table}', 1)[0]
    for method, printed_name in [('unmodified', '未処理'), ('both', '両規則'),
                                 ('binaryen-local', 'Binaryen局所'), ('binaryen-O2', 'Binaryen O2')]:
        values = [next(row['median_hps'] for row in summary['rows']
                       if row['cohort'] == 'development' and row['source'] == source and row['method'] == method)
                  for source in ['046dc081-roundtrip', '046dc081-nop10', '046dc081-constsplit10']]
        assert printed_name + ' & ' + ' & '.join(f'{value:.2f}' for value in values) in table
    for phrase in ('計138回測定', '同一SHAは測定を共有', '1.0276', '0.9943',
                   '0.9827--1.0120', '原因は未特定', '有効な対策の完成は示さない'):
        assert phrase in tex
    claims = []
    for filename in ['proof-of-theft/xmr-repeated-summary.json', 'swamped/controlled-pair-summary.json']:
        path = ROOT / 'results/runtime-mining/cross-dataset' / filename
        rows = json.loads(path.read_text(encoding='utf-8'))
        for row in rows:
            for key in ['median_hps', 'min_hps', 'max_hps']:
                printed = f'{row[key]:.2f}'
                assert printed in tex, (filename, row, key)
                claims.append(dict(source=str(path.relative_to(ROOT)), artifact=row.get('method', row.get('name')), key=key, value=row[key], printed=printed))
            printed = f"{row['instruction_ratio']:.3f}"
            assert printed in tex
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    compilation = json.loads((OUT / 'current-compilation.json').read_text(encoding='utf-8'))
    assert compilation['source_sha256'] == sha(ROOT / 'paper/main.tex')
    assert compilation['bibliography_sha256'] == sha(ROOT / 'paper/references.bib')
    assert compilation['pdf_sha256'] == sha(ROOT / 'paper/main.pdf')
    assert compilation['log_sha256'] == sha(ROOT / 'paper/main.log')
    assert compilation['compilation_verified'] and 6 <= compilation['pages'] <= 8
    report = dict(status='shortened manuscript checks and current compilation passed',
                  paper_sha256=compilation['source_sha256'], bibliography_sha256=compilation['bibliography_sha256'],
                  compilation_verified=True, page_count_verified=True, pages=compilation['pages'],
                  checks=['current citation keys and labels', 'RQ1/RQ2 and measured-artifact scope', 'figure files', 'XMR and SWAMPED printed rates and instruction ratios', '144 SHA-linked interface conditions and 72 dedicated conditions; function/resource equality claims', 'static feature-loss counts and evaluator SHA', 'additional 23-SHA, 72-label, 138-block measurement binding and all 12 printed development rate cells', 'current source/PDF/log digests and page range'],
                  additional_runtime_summary_sha256=sha(run / 'summary.json'),
                  runtime_claim_entries=len(claims), scope='Checks selected printed runtime figures, saved interface audit records, artifact/evaluator SHA links and source structure; prior detailed static-statistic audit is retained separately. Not independent parser or semantic review.',
                  remaining='Human interpretation review and separately pending experiments; no claim of completed research goal.')
    (OUT / 'compact-paper-claim-evidence.json').write_text(json.dumps(claims, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'paper-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    main()
