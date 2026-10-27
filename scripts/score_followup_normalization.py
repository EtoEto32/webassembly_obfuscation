"""Score all frozen exact-match tasks without executing or rewriting Wasm."""
import json
import time
from collections import Counter,defaultdict
from pathlib import Path
from evaluate_followup_normalization import ROOT,OUT,sha,read_plan


def main():
    pp,plan=read_plan();fp=OUT/'normalization-function-features.json';features=json.loads(fp.read_text(encoding='utf-8'))
    assert features['status']=='all-auxiliary-core-content-matches-real-outputs'
    sp=OUT/'normalization-static.json';static=json.loads(sp.read_text(encoding='utf-8'));assert features['static_result_sha256']==sha(sp)
    destination=OUT/'normalization-matching-results.json';assert not destination.exists()
    function_records=[];module_records=[];summaries=[]
    for method in plan['methods']:
        identifier=method['id'];index=defaultdict(list);reference_origins={};module_index=defaultdict(list)
        for reference in plan['references']:
            row=next(r for r in features['rows'] if r['input_id']==reference and r['method']==identifier)
            reference_origins[row['family']]={f['origin_index'] for f in row['functions'] if f['origin_index'] is not None}
            for f in row['functions']:index[f['fingerprint']].append(dict(reference_id=reference,family=row['family'],origin_index=f['origin_index'],position=f['output_definition_position']))
            r=next(r for r in static['records'] if r['input_id']==reference and r['method']==identifier)
            module_index[r['canonical_sha256']].append(reference)
        for item in plan['inputs']:
            if item['id'] in plan['references']:continue
            row=next(r for r in features['rows'] if r['input_id']==item['id'] and r['method']==identifier)
            by_origin=defaultdict(list)
            for f in row['functions']:
                if f['origin_index'] is not None:by_origin[f['origin_index']].append(f)
            for origin in features['origins'][item['id']]:
                base=dict(input_id=item['id'],method=identifier,origin_index=origin,truth_scope=item['truth'],
                    expected_reference=item['family']+'-baseline',reference_origin_retained=origin in reference_origins[item['family']])
                query=by_origin[origin]
                if len(query)!=1:
                    function_records.append(dict(**base,outcome='query_origin_not_retained' if not query else 'query_origin_ambiguous',candidates=[],lookup_ns=None));continue
                started=time.perf_counter_ns();candidates=list(index.get(query[0]['fingerprint'],[]));elapsed=time.perf_counter_ns()-started
                correct=any(c['family']==item['family'] and c['origin_index']==origin for c in candidates)
                outcome=('correct_unique' if correct else 'wrong_unique') if len(candidates)==1 else (
                    ('ambiguous_with_correct' if correct else 'ambiguous_without_correct') if candidates else 'unmatched')
                function_records.append(dict(**base,outcome=outcome,candidates=candidates,lookup_ns=elapsed))
            r=next(r for r in static['records'] if r['input_id']==item['id'] and r['method']==identifier)
            started=time.perf_counter_ns();candidates=list(module_index.get(r['canonical_sha256'],[]));elapsed=time.perf_counter_ns()-started
            expected=item['family']+'-baseline'
            outcome=('correct_unique' if expected in candidates else 'wrong_unique') if len(candidates)==1 else ('ambiguous' if candidates else 'unmatched')
            module_records.append(dict(input_id=item['id'],method=identifier,expected_reference=expected,candidates=candidates,outcome=outcome,lookup_ns=elapsed))
        selected=[r for r in function_records if r['method']==identifier];counts=Counter(r['outcome'] for r in selected)
        retained=sum(r['lookup_ns'] is not None for r in selected);assert len(selected)==features['fixed_queries_per_method']
        summaries.append(dict(method=identifier,fixed_function_queries=len(selected),retained_function_queries=retained,
            outcomes=dict(counts),correct_unique_over_fixed=counts['correct_unique']/len(selected),
            correct_unique_over_retained=counts['correct_unique']/retained if retained else None,
            reference_origin_not_retained=sum(not r['reference_origin_retained'] for r in selected),
            function_lookup_ns=sum(r['lookup_ns'] or 0 for r in selected),
            module_outcomes=dict(Counter(r['outcome'] for r in module_records if r['method']==identifier))))
    assert len(module_records)==56 and len(function_records)==features['fixed_queries_per_method']*7
    result=dict(status='all-frozen-matching-queries-scored',summaries=summaries,function_records=function_records,module_records=module_records,
        plan_sha256=sha(pp),feature_file_sha256=sha(fp),static_result_sha256=sha(sp),evaluator_sha256=sha(Path(__file__)),
        limits=['Shared ancestry/development controls; not held-out families.',
            'Exact syntax matching does not establish semantic equivalence or human analysis ease.',
            'Removed/untracked origins stay in the fixed denominator; retained-only rates are conditional.',
            'Lookup-only wall times are descriptive; exclude preprocessing, feature extraction and grading.',
            'No detector or new throughput evaluation.'],runtime_executed=False)
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],function_queries=len(function_records),module_queries=len(module_records),summaries=summaries),indent=2))


if __name__=='__main__':main()
