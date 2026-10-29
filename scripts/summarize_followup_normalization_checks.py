"""Aggregate only completed audited normalization checks; retain the OOM history."""
import json
from collections import Counter
from pathlib import Path
from audit_normalization_resources import canonical
from evaluate_followup_normalization import ROOT,OUT,sha,read_plan


def main():
    pp,plan=read_plan();target=OUT/'normalization-output-audit.json';assert not target.exists()
    execution_path=next((OUT/'normalization-execution-v2').glob('*/status.json'))
    execution=json.loads(execution_path.read_text(encoding='utf-8'));assert execution['status']=='stage-complete' and len(execution['batches'])==9
    manifest_path=OUT/'normalization-check-plans-v2.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    assert execution['manifest_sha256']==sha(manifest_path) and manifest['labels']==77
    sp=OUT/'normalization-static.json';static=json.loads(sp.read_text(encoding='utf-8'));assert static['status']=='static-validation-complete'
    wanted={r['input_id']+'--'+r['method']:r for r in static['records']};seen={};sources=[];counts=Counter();additional=None
    for batch in execution['batches']:
        run=ROOT/batch['run'];ap=run/'controlled-audit.json';a=json.loads(ap.read_text(encoding='utf-8'));rp=run/'outputs/controlled-checks.json'
        assert a['status']=='passed' and sha(ap)==batch['audit_sha256'] and sha(rp)==a['measurement_sha256']
        raw=json.loads(rp.read_text(encoding='utf-8'));assert raw['status']=='complete'
        cp=run/'inputs/plan.json';p=json.loads(cp.read_text(encoding='utf-8'));assert sha(cp)==a['plan_sha256']==raw['plan_sha256']
        assert p['controlled']['normalization_plan_sha256']==sha(pp) and p['controlled']['static_result_sha256']==sha(sp)
        current_additional=[(v['id'],v['hex'],v['expected']) for v in raw['additional_vectors']]
        if additional is None:additional=current_additional
        else:assert additional==current_additional
        for artifact in p['controlled']['artifacts']:
            key=artifact['id'];assert key in wanted and key not in seen and artifact['sha256']==wanted[key]['sha256']
            assert sha(ROOT/wanted[key]['path'])==artifact['sha256'];seen[key]=dict(sha256=artifact['sha256'],run=batch['run'])
        c=json.loads((run/'completion.json').read_text(encoding='utf-8'));assert c['exit_code']==0 and not c['state']['OOMKilled']
        counts.update(checks=a['checks'],public=a['public_checks'],reference_derived=a['reference_derived_checks'])
        sources.append(dict(run=batch['run'],reused=batch['reused'],audit_sha256=sha(ap),measurement_sha256=sha(rp),checks=a['checks']))
    assert set(seen)==set(wanted) and counts==Counter(checks=2793,public=945,reference_derived=1848)
    resource_checks=[]
    for row in static['records']:
        original=next(r for r in static['records'] if r['input_id']==row['input_id'] and r['method']=='unmodified')
        function_exports=canonical(row['signatures']['exported_functions'])==canonical(original['signatures']['exported_functions'])
        resource_exports=canonical(row['resources']['exported_resources'])==canonical(original['resources']['exported_resources'])
        assert function_exports and resource_exports
        dedicated=row['method'] in ['nop','integer-fold','both']
        if dedicated:assert row['signatures']==original['signatures'] and row['resources']==original['resources']
        resource_checks.append(dict(input_id=row['input_id'],method=row['method'],exported_function_types_equal=function_exports,
            exported_resource_types_limits_equal=resource_exports,dedicated_full_interface_and_resource_types_equal=True if dedicated else None))
    result=dict(status='all-77-labels-output-and-interface-audited',labels=77,unique_sha256=len({r['sha256'] for r in seen.values()}),
        output_checks=counts['checks'],public_expected_checks=counts['public'],reference_derived_checks=counts['reference_derived'],
        sources=sources,labels_by_source=seen,resource_checks=resource_checks,static_result_sha256=sha(sp),
        normalization_plan_sha256=sha(pp),revised_manifest_sha256=sha(manifest_path),execution_status_sha256=sha(execution_path),
        preserved_oom_run=manifest['preserved_oom_run'],successful_swamped_reused=True,
        evaluator_sha256=sha(Path(__file__)),limits=['Finite 76-byte input/state tests, not whole-module equivalence.',
            'Repeated labels converging to the same SHA are not independent implementations or independent successes.',
            'Public expectations and reference-derived expectations have different evidential scope.',
            'Resource audit checks types/limits, not complete initial memory/table contents or all host effects.'])
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ['status','labels','unique_sha256','output_checks','public_expected_checks','reference_derived_checks']},indent=2))


if __name__=='__main__':main()
