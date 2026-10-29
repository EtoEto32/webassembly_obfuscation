"""Persist phase/evidence locations without claiming a live process from stale IDs."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def main():
    runs=[]
    for folder in sorted((OUT/'runs').iterdir()):
        row=dict(directory=str(folder.relative_to(ROOT)).replace('\\','/'))
        for filename in ['completion.json','failure.json','launch.json']:
            path=folder/filename
            if path.exists():
                data=json.loads(path.read_text(encoding='utf-8'))
                if filename=='completion.json':row['completion']=dict(exit_code=data['exit_code'],elapsed_seconds=data['elapsed_seconds'])
                if filename=='failure.json':row['failure']=data['error']
                if filename=='launch.json':row['container_id']=data['container_id']
        runtime=folder/'outputs/runtime.json'
        if runtime.exists():
            data=json.loads(runtime.read_text(encoding='utf-8'));row['recorded_runtime_status']=data['status'];row['completed_blocks']=len(data['samples'])
            row['liveness_note']='Confirm the exec session or container state; a saved running status alone does not prove liveness.'
        runs.append(row)
    executions=[]
    for path in sorted((OUT/'confirmatory-execution').glob('*/status.json')) if (OUT/'confirmatory-execution').exists() else []:
        executions.append(dict(path=str(path.relative_to(ROOT)),recorded_status=json.loads(path.read_text(encoding='utf-8'))))
    checkpoint=dict(recorded_utc=datetime.now(timezone.utc).isoformat(),goal_status='active; incomplete',
        policy='Preserve existing research, evaluate structure/correctness/performance first, then consider normalization. No novel obfuscator or detector-improvement requirement.',
        input_contract_audit='results/followup-evaluation-20261016/input-audit.json',
        runtime_pilot_plan='results/followup-evaluation-20261016/runtime-pilot-plan.json',
        path_plan='results/followup-evaluation-20261016/path-plan.json',
        controlled_check_plan='results/followup-evaluation-20261016/controlled-check-plan.json',
        progress_report='docs/followup-evaluation-progress-20261016.md',
        performance_report='docs/followup-performance-results-20261016.md',
        normalization_report='docs/followup-normalization-results-20261016.md',
        reproduction_guide='docs/followup-reproduction-20261016.md',
        paper_reflection_proposal='docs/paper-followup-reflection-20261016.md',
        runs=runs,confirmatory_executions=executions,
        post_performance_executions=[dict(path=str(p.relative_to(ROOT)),recorded_status=json.loads(p.read_text(encoding='utf-8')))
            for p in sorted((OUT/'post-performance').glob('*/status.json'))],
        inherited_evidence_index='results/followup-evaluation-20261016/inherited-evidence-index.json',
        completed_analysis_files=[str(p.relative_to(ROOT)).replace('\\','/') for p in [
            OUT/'confirmatory-summary.json',OUT/'confirmatory-structure.json',OUT/'callsite-summary.json',
            OUT/'post-performance-recovery.json',OUT/'figures/confirmatory-visual-review.json',
            OUT/'normalization-plan.json',OUT/'normalization-static.json',OUT/'normalization-output-audit.json',
            OUT/'normalization-function-features.json',OUT/'normalization-matching-results.json',
            OUT/'normalization-helper-truth/checks.json',OUT/'figures/normalization-visual-review.json'] if p.exists()],
        normalization_executions=[dict(path=str(p.relative_to(ROOT)),recorded_status=json.loads(p.read_text(encoding='utf-8')))
            for directory in ['normalization-execution','normalization-execution-v2','normalization-replays']
            for p in sorted((OUT/directory).glob('*/status.json'))],
        analysis_scripts=['scripts/summarize_followup_confirmatory.py','scripts/measure_followup_structure.py',
            'scripts/summarize_followup_callsites.py','scripts/plot_followup_confirmatory.py'],
        completed_evidence=dict(input_contract='input-audit.json',
            pilot='runs/runtime-bd69ee8d729c4792823d9f3860c5c0c6/pilot-audit.json; correctness passed, requested Liftoff-only mode failed',
            corrected_compiler_probe='compiler-probe-audit.json',
            function_counts='runs/input-diagnostic-bcebbc1a56fe4253b48b3b95e2911d9e/paths-audit.json',
            controlled_correctness='runs/input-diagnostic-7d69953eb3d44538929da22fe95b4b63/controlled-audit.json'),
        confirmatory_plans='results/followup-evaluation-20261016/confirmatory-plans.json',
        callsite_plan='results/followup-evaluation-20261016/callsite-plan.json',
        pending=['Finish/verify the separate seven-label-batch reproducibility replay; revalidate its live exec handle before any restart.',
            'Complete integrated report, final paper reflection/abstract proposal and reproduction guide using the actual normalization results.',
            'Run requirement-by-requirement completion audit, including source preservation, primary evidence and figure reviews.'],
        original_paper_modified=False,goal_complete=False)
    completion_path=OUT/'completion-audit.json'
    if completion_path.exists():
        completion=json.loads(completion_path.read_text(encoding='utf-8'))
        import hashlib
        intact=all(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in completion['evidence_hashes'])
        if completion['status']=='all-requirements-proved-with-stated-scope' and intact:
            checkpoint.update(goal_status='research objective audited complete; application goal state is governed by update_goal',
                goal_complete=True,pending=[],completion_audit='results/followup-evaluation-20261016/completion-audit.json',
                completion_audit_sha256=hashlib.sha256(completion_path.read_bytes()).hexdigest(),
                integrated_report='docs/followup-research-report-20261016.md')
    destination=OUT/'checkpoint.json';destination.write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(checkpoint=str(destination),runs=runs),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
