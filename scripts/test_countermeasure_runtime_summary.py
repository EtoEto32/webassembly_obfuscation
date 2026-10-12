"""In-memory artificial logs test rejection rules; never save fabricated measurements."""
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from summarize_countermeasure_runtime import ROOT, review_measurement, aggregate, sha


def main():
    plan=json.loads((ROOT/'results/countermeasures/runtime-preparation/plan.json').read_text(encoding='utf-8'))
    public=plan['public_vectors']
    oracle={v['id']:'a1'*32 for v in plan['additional_vectors']}
    def checks(vectors, expected=None):
        return [dict(id=v['id'],actual=expected[v['id']] if expected else v['expected'],
                     expected=expected[v['id']] if expected else v['expected'],matches=True) for v in vectors]
    report=dict(status='complete',node=plan['environment']['intended_node'],v8=plan['environment']['intended_v8'],
        image_id=plan['environment']['image'],cpu_model='synthetic fixture only',
        baseline_oracle=dict(public_checks=checks(public),additional_outputs=oracle,
            additional_outputs_by_order={'forward':oracle,'reverse':oracle},fresh_additional_outputs=oracle),
        public_checks=[],additional_checks=[],fresh_additional_checks=[],samples=[])
    for artifact in plan['artifacts']:
        report['fresh_additional_checks'].append(dict(artifact_id=artifact['id'],checks=checks(plan['additional_vectors'],oracle)))
        for reverse in [False,True]:
            report['public_checks'].append(dict(artifact_id=artifact['id'],reverse=reverse,checks=checks(public)))
            vectors=list(reversed(plan['additional_vectors'])) if reverse else plan['additional_vectors']
            report['additional_checks'].append(dict(artifact_id=artifact['id'],reverse=reverse,checks=checks(vectors,oracle)))
    epoch=datetime(2020,1,1,tzinfo=timezone.utc)
    for index, entry in enumerate(plan['measurement']['schedule']):
        count=600+index
        last=public[(count-1)%len(public)]
        start=epoch+timedelta(seconds=index*33)
        report['samples'].append(dict(entry,count=count,elapsed_ms=30000.,hashes_per_second=count/30.,
            warmup_count=60,warmup_elapsed_ms=3000.,
            final_output=last['expected'],final_expected=last['expected'],pre_checks=checks(public),post_checks=checks(public),
            started_utc=start.isoformat(),finished_utc=(start+timedelta(seconds=31)).isoformat()))
    samples=review_measurement(plan,report)
    rows=aggregate(plan,samples)
    assert len(rows)==72 and len(samples)==138
    for row in rows:
        if row['method']=='unmodified':
            assert row['same_input_unmodified_median_rate_ratio']==1
            assert row['same_input_unmodified_round_ratio_min']==row['same_input_unmodified_round_ratio_max']==1
    checks_passed=['complete artificial protocol accepted without saving measurement data',
                   '72 labels mapped to 23 artifact measurements; unmodified self ratios equal one']
    mutations={
        'failed status':lambda r:r.update(status='failed'),
        'failure evidence':lambda r:r.update(failed_check={'actual':'bad'}),
        'wrong runtime':lambda r:r.update(node='incorrect'),
        'missing additional oracle':lambda r:r['baseline_oracle']['additional_outputs'].pop(next(iter(oracle))),
        'missing artifact checks':lambda r:r['public_checks'].pop(),
        'wrong output':lambda r:r['public_checks'][0]['checks'][0].update(actual='00'*32),
        'wrong additional order':lambda r:r['additional_checks'][1]['checks'].reverse(),
        'missing block':lambda r:r['samples'].pop(),
        'duplicated block':lambda r:r['samples'].__setitem__(1,copy.deepcopy(r['samples'][0])),
        'zero count':lambda r:r['samples'][0].update(count=0),
        'no warmup hashes':lambda r:r['samples'][0].update(warmup_count=0),
        'short warmup':lambda r:r['samples'][0].update(warmup_elapsed_ms=1.),
        'short interval':lambda r:r['samples'][0].update(elapsed_ms=100.),
        'NaN interval':lambda r:r['samples'][0].update(elapsed_ms=float('nan')),
        'wrong rate':lambda r:r['samples'][0].update(hashes_per_second=999.),
        'wrong final hash':lambda r:r['samples'][0].update(final_output='00'*32),
        'missing post check':lambda r:r['samples'][0]['post_checks'].pop(),
        'overlapping blocks':lambda r:r['samples'][1].update(started_utc=r['samples'][0]['started_utc']),
    }
    for name, mutate in mutations.items():
        candidate=copy.deepcopy(report);mutate(candidate)
        try:review_measurement(plan,candidate)
        except ValueError:checks_passed.append('rejected '+name)
        else:raise AssertionError('Accepted invalid artificial log: '+name)
    result=dict(checks=checks_passed,aggregator_sha256=sha(ROOT/'scripts/summarize_countermeasure_runtime.py'),
        test_sha256=sha(Path(__file__)),target_wasm_executed=False,real_measurements_saved=False,
        scope='Artificial protocol fixtures in memory only. Does not validate real performance, permission, or host semantics.')
    (ROOT/'results/countermeasures/runtime-preparation/summary-mock-checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(checks=len(checks_passed),target_wasm_executed=False,real_measurements_saved=False)))


if __name__=='__main__':
    main()
