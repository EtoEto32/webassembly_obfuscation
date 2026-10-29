"""Preserve the OOM run; split remaining labels without changing limits or vectors."""
import json
from evaluate_followup_normalization import ROOT,OUT,sha,read_plan


def main():
    target=OUT/'normalization-check-plans-v2.json';assert not target.exists();pp,protocol=read_plan()
    first=next((OUT/'normalization-execution').glob('*/status.json'));state=json.loads(first.read_text(encoding='utf-8'))
    assert state['status']=='failed' and len(state['batches'])==1 and state['batches'][0]['family']=='swamped'
    accepted=state['batches'][0];accepted_run=ROOT/accepted['run'];audit_path=accepted_run/'controlled-audit.json'
    audit=json.loads(audit_path.read_text(encoding='utf-8'));assert audit['status']=='passed' and audit['artifacts']==21 and audit['checks']==819
    assert sha(audit_path)==accepted['audit_sha256'] and sha(accepted_run/'outputs/controlled-checks.json')==audit['measurement_sha256']
    failed=OUT/'runs/input-diagnostic-9e7f9b4e659c4188a5b701dc53c23096';completion=json.loads((failed/'completion.json').read_text(encoding='utf-8'))
    assert completion['state']['OOMKilled'] and completion['exit_code']==137
    entries=[]
    for item in protocol['inputs']:
        family=item['family']
        if family=='swamped':continue
        original=OUT/('normalization-check-'+family+'-plan.json');plan=json.loads(original.read_text(encoding='utf-8'))
        all_outputs={a['file'] for a in plan['controlled']['artifacts']}
        cases=[a for a in plan['controlled']['artifacts'] if a['id'].startswith(item['id']+'--')];assert len(cases)==7
        selected={a['file'] for a in cases};plan['assets']=[a for a in plan['assets'] if a['name'] not in all_outputs or a['name'] in selected]
        plan['controlled'].update(artifacts=cases,batch_revision='v2; seven methods of one input per container after preserved OOM',
            unchanged_parent_plan_sha256=sha(original))
        path=OUT/('normalization-check-'+item['id']+'-v2-plan.json');assert not path.exists()
        path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        entries.append(dict(batch_id=item['id'],family=family,path=str(path.relative_to(ROOT)).replace('\\','/'),sha256=sha(path),labels=7))
    assert len(entries)==8 and 21+sum(e['labels'] for e in entries)==77
    manifest=dict(frozen_before_execution=True,plans=entries,labels=77,new_labels=56,
        reused=dict(family='swamped',labels=21,run=accepted['run'],audit_sha256=sha(audit_path)),
        reason='Original xmr batch was killed at the unchanged 1GiB container limit; no output mismatch was recorded. Split remaining eight inputs into seven-method batches; all 77 planned labels retained.',
        preserved_failed_execution=str(first.relative_to(ROOT)),failed_execution_sha256=sha(first),
        preserved_oom_run=str(failed.relative_to(ROOT)),oom_completion_sha256=sha(failed/'completion.json'),
        unchanged_runtime_limits=True,unchanged_binaries=True,unchanged_vectors_and_modes=True,
        normalization_plan_sha256=sha(pp),goal_complete=False)
    target.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8');print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
