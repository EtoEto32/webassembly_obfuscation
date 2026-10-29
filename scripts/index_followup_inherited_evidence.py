"""Verify reusable saved evidence without relabeling old runs as new experiments."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/countermeasures'
OUT=ROOT/'results/followup-evaluation-20261016/inherited-evidence-index.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():raise RuntimeError('Preserve previous evidence index')
    normalizer=ROOT/'scripts/normalize_wat_local.py';normalizer_sha=sha(normalizer)
    rows=[];all_static=[]
    for relative,count in [('local-normalization/static-comparison.json',18),('transfer/comparison.json',72),('seeded-normalization/comparison.json',54)]:
        path=BASE/relative;data=json.loads(path.read_text(encoding='utf-8'));assert len(data['records'])==count
        code_matches=data['normalizer_sha256']==normalizer_sha
        artifact_matches=[]
        for item in data['records']:
            p=ROOT/item['path'];assert sha(p)==item['sha256'];artifact_matches.append(item['sha256'])
        all_static.extend(data['records'])
        rows.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),records=count,
            current_normalizer_matches_recorded_sha256=code_matches,
            actual_normalizer_sha256=normalizer_sha,recorded_normalizer_sha256=data['normalizer_sha256'],
            recorded_output_artifact_hashes_verified=len(artifact_matches),scope=data['scope']))
    synthetic_path=BASE/'local-normalization/synthetic-tests/result.json'
    synthetic=json.loads(synthetic_path.read_text(encoding='utf-8'));assert synthetic['status']=='passed'
    rows.append(dict(path=str(synthetic_path.relative_to(ROOT)),sha256=sha(synthetic_path),functions=synthetic['functions'],
        recorded_runtime_checks=synthetic['runtime']['checked'],current_normalizer_matches_recorded_sha256=synthetic['normalizer_sha256']==normalizer_sha,
        scope=synthetic['scope']))
    dedicated={'nop','integer-fold','both'}
    assert sum(r['variant'] in dedicated for r in all_static)==72
    for relative,fields in [('interface-signature-audit.json',['function_signatures_equal','exported_function_signatures_equal','interface_names_kinds_equal']),
            ('interface-resource-audit.json',['imported_resources_equal','exported_resources_equal','defined_resource_types_equal'])]:
        path=BASE/relative;data=json.loads(path.read_text(encoding='utf-8'));assert len(data['records'])==144
        selected=[r for r in data['records'] if r['variant'] in dedicated];assert len(selected)==72
        assert all(r[field] for r in selected for field in fields)
        rows.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),records=144,dedicated_conditions=72,
            recorded_dedicated_properties_verified=fields,scope=data['scope']))
    for relative in ['flattening-xor/checks.json','flattening-xor/state-model-checks.json','expression-analysis/extracted-output-checks.json']:
        path=BASE/relative;data=json.loads(path.read_text(encoding='utf-8'));assert data['passed'] is True
        if relative.startswith('flattening-xor'):
            assert all(r['matched'] for r in data['records'])
        if 'cases_sha256' in data:assert sha(BASE/'flattening-xor/cases.json')==data['cases_sha256']
        if 'wasm_sha256' in data:assert sha(BASE/'flattening-xor/isolated-xor.wasm')==data['wasm_sha256']
        for record in data['records']:
            if 'detail_sha256' in record:assert sha(ROOT/record['detail'])==record['detail_sha256']
        rows.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),recorded_pass=True,
            cases=data.get('cases'),helper_calls=data.get('helper_calls'),expressions=data.get('expressions'),
            integer_checks=data.get('integer_checks'),scope=data['scope']))
    path=BASE/'detector-feasibility/scale-sensitivity.json';data=json.loads(path.read_text(encoding='utf-8'))
    rows.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),summary=data['summary'],
        trained_model_provenance_unresolved=data['trained_model_provenance_unresolved'],scope=data['scope']))
    result=dict(status='saved-records-and-referenced-hashes-verified',records=rows,
        current_normalizer_sha256=normalizer_sha,total_static_conditions=144,dedicated_conditions=72,
        new_wasm_executions=0,old_results_not_reclassified_as_new=True,
        limits=['Hashes and recorded pass fields establish correspondence, not independent reruns or all-input correctness.',
            'Synthetic/isolated tests and detector preprocessing do not prove whole-miner behavior or detector improvements.'],
        index_script_sha256=sha(Path(__file__)))
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],files=len(rows),static_conditions=144,dedicated_conditions=72,
        normalizer_source_matches=[r.get('current_normalizer_matches_recorded_sha256') for r in rows if 'current_normalizer_matches_recorded_sha256' in r]),indent=2))


if __name__=='__main__':main()
