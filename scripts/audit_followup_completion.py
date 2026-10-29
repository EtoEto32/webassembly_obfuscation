"""Requirement-level evidence audit. Reads real artifacts; never executes Wasm."""
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from evaluate_followup_normalization import ROOT,OUT,sha,read_plan
from prepare_followup_function_task import core,fingerprint,functions,type_shapes


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def run_evidence(run,successful=True):
    p=read(run/'inputs/plan.json');launch=read(run/'launch.json');inspect=read(run/'container-inspect.json')
    assert sha(run/'inputs/plan.json')==launch['plan_sha256']
    permission=ROOT/'results/countermeasures/runtime-preparation/professor-permission.json'
    assert read(permission)['confirmed'] and sha(permission)==p['authorization']['inherited_professor_permission_sha256']
    assert p['authorization']['user_request']
    h=inspect['HostConfig'];assert inspect['Image']==p['image']=='sha256:a05286e66b0f1ca712671db5849229594c92e035bae253362cc8b6d0af4a70b6'
    assert h['NetworkMode']=='none' and h['NanoCpus']==10**9 and h['CpusetCpus']=='0'
    assert h['Memory']==h['MemorySwap']==1024**3 and h['PidsLimit']==64 and h['ReadonlyRootfs']
    assert inspect['Config']['User']=='10001:10001' and 'ALL' in h['CapDrop']
    assert any(x.startswith('no-new-privileges') for x in h['SecurityOpt'])
    mounts={m['Destination']:m for m in inspect['Mounts']};assert not mounts['/inputs']['RW'] and mounts['/outputs']['RW']
    for a in p['assets']:
        assert sha(ROOT/a['path'])==a['sha256'] and sha(run/'inputs'/a['name'])==a['sha256']
    c=read(run/'completion.json')
    if successful:assert c['exit_code']==c['state']['ExitCode']==0 and not c['state']['OOMKilled'] and not c['state']['Running']
    return p,c


def main():
    target=OUT/'completion-audit.json';assert not target.exists()
    requirements=[];evidence_files=set()
    def add(identifier,requirement,files,observations,limits=None):
        paths=[ROOT/p if not Path(p).is_absolute() else Path(p) for p in files]
        for p in paths:assert p.is_file();evidence_files.add(p)
        requirements.append(dict(id=identifier,requirement=requirement,status='proved-with-stated-scope',
            evidence=[str(p.relative_to(ROOT)).replace('\\','/') for p in paths],observations=observations,limits=limits or []))
    # Preserve original work, including original generated artifacts referenced in the inherited records.
    index_path=OUT/'inherited-evidence-index.json';index=read(index_path)
    assert index['total_static_conditions']==144 and index['dedicated_conditions']==72
    assert sha(ROOT/'scripts/normalize_wat_local.py')==index['current_normalizer_sha256']=='01af604b04e54026c9b53c5b70e6cb89ee9e8e2424890c28305b5bd62cad58d9'
    old_artifacts=0
    for row in index['records']:
        p=ROOT/row['path'];assert sha(p)==row['sha256'];evidence_files.add(p)
        if row.get('recorded_output_artifact_hashes_verified'):
            d=read(p)
            for artifact in d['records']:assert sha(ROOT/artifact['path'])==artifact['sha256'];old_artifacts+=1
    assert old_artifacts==144
    diff=subprocess.run(['git','diff','HEAD','--quiet','--','paper/main.tex','scripts/normalize_wat_local.py'],cwd=ROOT)
    assert diff.returncode==0
    add('inheritance','Preserve existing research, paper, normalizer and evidence.',
        [index_path,ROOT/'paper/main.tex',ROOT/'scripts/normalize_wat_local.py'],dict(original_records=len(index['records']),referenced_static_artifacts=144,normalizer_unchanged=True,paper_git_diff_empty=True),
        ['Old results were hash-verified, not all rerun or reclassified as new.'])
    # Input contract: current raw record, execution limits and static entry agree with the audit.
    ia=read(OUT/'input-audit.json');assert ia['status']=='passed'
    ir=ROOT/ia['audited_run'];p,c=run_evidence(ir)
    assert sha(ir/'outputs/input-diagnostic.json')==ia['measurement_sha256'] and sha(ir/'inputs/plan.json')==ia['plan_sha256']
    assert [ia[k] for k in ['target_public_checks','length_argument_checks','history_checks','unique_effective_inputs_with_webminerpool_reference']]==[15,27,81,14]
    contract=read(OUT/'static-input-contract.json');wp=ROOT/'results/runtime-mining/cross-dataset/swamped/046dc081-roundtrip.wat'
    assert sha(wp)==contract['wat_sha256'];lines=wp.read_text(encoding='utf-8').splitlines();body=lines[contract['function_first_line']-1:]
    assert body[2:4]==['    global.get $g4','    local.set $p3'];end=body.index('    i32.load offset=72 align=1')
    offsets=[int(m[1] or 0) for l in body[:end+1] if (m:=re.fullmatch(r'    i64.load(?: offset=(\d+))? align=1',l))]
    assert offsets==list(range(0,72,8))
    add('input-contract','Explain the observed short-input history and preserve the scope of correctness claims.',
        [OUT/'input-audit.json',OUT/'static-input-contract.json',ir/'outputs/input-diagnostic.json'],
        dict(fixed_bytes=76,length_checks=27,history_checks=81,public_checks=15,effective_reference_inputs=14),
        ['Three selected SWAMPED binaries; finite inputs and shared reference lineage, not arbitrary-length validation.'])
    # Strictly inspect every timed block and trace, not just the stored pass labels.
    summary_path=OUT/'confirmatory-summary.json';summary=read(summary_path);assert summary['timed_blocks']==272 and summary['paired_contrasts']==108
    assert sha(ROOT/'scripts/summarize_followup_confirmatory.py')==summary['summary_script_sha256']
    compilers=Counter();blocks=0;trace_records={}
    pattern=re.compile(r'Compiled function \S+#(\d+) using (\w+), took (\d+) ms and (\d+)(?: / \d+ max/total)? bytes; bodysize (\d+) codesize (\d+)')
    for source in summary['sources']:
        run=ROOT/source['run'];plan,completion=run_evidence(run);raw_path=run/'outputs/runtime.json';audit_path=run/'confirmatory-audit.json'
        raw=read(raw_path);a=read(audit_path);assert a['status']=='passed' and sha(audit_path)==source['audit_sha256']
        assert sha(raw_path)==source['measurement_sha256']==a['measurement_sha256'] and sha(run/'inputs/plan.json')==source['plan_sha256']
        assert a['auditor_sha256']==sha(ROOT/'scripts/audit_followup_confirmatory.py')
        assert raw['status']=='complete' and len(raw['samples'])==len(plan['runtime']['schedule'])
        for expected,s in zip(plan['runtime']['schedule'],raw['samples']):
            assert all(s[k]==v for k,v in expected.items())
            assert s['elapsed_ms']>=30000 and s['warmup_ms']>=5000 and s['count']>0
            assert abs(s['hashes_per_second']-s['count']*1000/s['elapsed_ms'])<1e-9
            assert s['final_output']==s['final_expected'] and s['final_nonce_unchanged']
            assert all(c['actual']==c['expected'] and c['nonce_unchanged'] for k in ['pre_checks','post_checks'] for c in s[k])
            trace=run/'outputs'/(str(s['sequence']).zfill(3)+'-stdout.txt');text=trace.read_text(encoding='utf-8');lines=text.splitlines()
            kinds=set(re.findall(r'using (Liftoff|TurboFan),',text));assert kinds==({'Liftoff'} if s['mode']=='liftoff' else {'TurboFan'})
            start=next(i for i,l in enumerate(lines) if l.startswith('FOLLOWUP_PHASE timed-start'));stop=next(i for i,l in enumerate(lines) if l.startswith('FOLLOWUP_PHASE timed-end'))
            assert stop>start and not any(l.startswith('Compiled function ') for l in lines[start+1:stop])
            records=pattern.findall(text);assert len(records)==sum(l.startswith('Compiled function ') for l in lines)
            trace_records[s['session'],s['sequence']]=sum(int(r[5]) for r in records)
            compilers.update(kinds);blocks+=1
    assert blocks==272 and compilers==Counter(Liftoff=136,TurboFan=136)
    for r in summary['compiled_code_blocks']:assert r['reported_code_bytes']==trace_records[r['session'],r['sequence']]
    assert len(summary['summaries'])==18 and all(len(r['ratios_by_repetition'])==6 for r in summary['summaries'])
    assert all(len(r['session_geometric_ratios'])==3 for r in summary['summaries'])
    pilot=OUT/'runs/runtime-bd69ee8d729c4792823d9f3860c5c0c6/pilot-audit.json';assert read(pilot)['status']=='measurement-checks-passed-with-compiler-mode-deviation'
    assert read(OUT/'compiler-probe-audit.json')['status']=='passed'
    add('performance','Measure, audit and analyze before/after performance, variability and Wasm compiler conditions.',
        [summary_path,OUT/'confirmatory-structure.json',pilot,OUT/'compiler-probe-audit.json'],
        dict(timed_blocks=272,contrasts=108,compilers=dict(compilers),timed_wasm_compilation_events=0,all_planned_repetitions_retained=True),
        ['JavaScript JIT is not traced. Consecutive sessions, one host, pointwise exploratory intervals and remaining baseline variation limit inference.'])
    # Dynamic entry counts, call-site accounting and manual ablation have distinct scope.
    ca=read(OUT/'callsite-summary.json');assert ca['status']=='audited-site-sums-match-helper-entry-counts' and len(ca['records'])==9
    for r in ca['records']:
        assert r['helper_entry_calls']==r['direct_callsite_total']==1179648 and r['unexplained_calls']==0
        if r['id']=='original':
            assert r['reviewed_original_loop_L17_calls']==1048576 and r['other_direct_calls']==131072
            assert r['L17_lexical_sites']==4 and r['L17_executed_sites']==2 and r['nested_L17_calls']==0
    recovery=read(OUT/'post-performance-recovery.json')
    assert sha(OUT/'callsite-summary.json')==recovery['callsite_summary_sha256'] and not recovery['wasm_rerun']
    assert sha(ROOT/recovery['original_failed_job_status'])==recovery['original_failed_status_sha256']
    paths=OUT/'runs/input-diagnostic-bcebbc1a56fe4253b48b3b95e2911d9e';run_evidence(paths);pa=read(paths/'paths-audit.json')
    assert pa['status']=='passed' and sha(paths/'outputs/paths.json')==pa['measurement_sha256']
    for r in pa['per_hash_counts']:assert r['counts']['f112']=='0' and r['counts']['f118']=='1179648'
    add('execution-paths','Separate unexecuted and frequent helpers and measure call-site coverage and ablation effects.',
        [OUT/'callsite-summary.json',OUT/'post-performance-recovery.json',paths/'paths-audit.json'],
        dict(counted_vector_conditions=9,xor8_calls=0,xor16_calls=1179648,original_main_loop_calls=1048576),
        ['Function entries/call sites are not dynamic instruction counts or time shares; restoration is manual, not automatic normalization.'])
    generation=read(OUT/'controlled-generation-v2.json');assert len(generation['cases'])==9
    assert sha(ROOT/'data/source/swamped/code_perturbation.py')==generation['source_sha256']
    for r in generation['cases']:assert sha(ROOT/r['path'])==r['sha256'] and sha(ROOT/r['input_path'])==r['input_sha256']
    control=OUT/'runs/input-diagnostic-7d69953eb3d44538929da22fe95b4b63';run_evidence(control);a=read(control/'controlled-audit.json')
    assert a['status']=='passed' and [a['checks'],a['public_checks'],a['reference_derived_checks']]==[333,117,216]
    assert sha(control/'outputs/controlled-checks.json')==a['measurement_sha256']
    add('multiple-implementations','Compare controlled transformations of multiple archived implementations.',
        [OUT/'controlled-generation-v2.json',control/'controlled-audit.json'],dict(inputs=9,implementations=3,correctness_checks=333),
        ['Same Wasm transformation/tool pipeline, not equalized original C/C++ builds. Shared CryptoNight ancestry.'])
    # Current normalized artifacts, actual core bytes and finite outputs.
    pp,plan=read_plan();static_path=OUT/'normalization-static.json';static=read(static_path);oa=read(OUT/'normalization-output-audit.json')
    assert static['status']=='static-validation-complete' and len(static['records'])==77
    assert oa['status']=='all-77-labels-output-and-interface-audited' and oa['static_result_sha256']==sha(static_path)
    assert [oa['labels'],oa['unique_sha256'],oa['output_checks'],oa['public_expected_checks'],oa['reference_derived_checks']]==[77,42,2793,945,1848]
    for r in static['records']:
        assert sha(ROOT/r['path'])==r['sha256'] and sha(ROOT/r['canonical_path'])==r['canonical_sha256']
    labels=set();counts=Counter()
    for source in oa['sources']:
        run=ROOT/source['run'];p,c=run_evidence(run);ap=run/'controlled-audit.json';a=read(ap);raw_path=run/'outputs/controlled-checks.json';raw=read(raw_path)
        assert a['status']=='passed' and sha(ap)==source['audit_sha256'] and sha(raw_path)==source['measurement_sha256']==a['measurement_sha256']
        assert raw['status']=='complete' and raw['plan_sha256']==sha(run/'inputs/plan.json')
        vectors={v['id']:v for v in p['public_vectors']+raw['additional_vectors']}
        wanted=[]
        for artifact in p['controlled']['artifacts']:
            assert artifact['id'] not in labels;labels.add(artifact['id'])
            for mode in p['controlled']['modes']:
                wanted.extend((artifact['id'],mode,v['id']) for v in vectors.values() if artifact['family']!='xmr-wasm' or bytes.fromhex(v['hex'])[0]<7)
        assert Counter((r['artifact_id'],r['mode'],r['vector_id']) for r in raw['checks'])==Counter(wanted)
        assert all(r['actual']==r['expected']==vectors[r['vector_id']]['expected'] for r in raw['checks'])
        counts.update(checks=len(raw['checks']))
    assert len(labels)==77 and counts['checks']==2793
    oom=OUT/'runs/input-diagnostic-9e7f9b4e659c4188a5b701dc53c23096';_,c=run_evidence(oom,False);assert c['exit_code']==137 and c['state']['OOMKilled']
    add('normalization-correctness','Compare unchanged rules with established optimizers and audit normalized results.',
        [pp,static_path,OUT/'normalization-output-audit.json',OUT/'normalization-check-plans-v2.json',oom/'completion.json'],
        dict(labels=77,unique_sha256=42,output_checks=2793,normalizer_unchanged=True,oom_preserved=True),
        ['Finite input checks and type/limit audits do not prove all-input or whole-module equivalence.'])
    features_path=OUT/'normalization-function-features.json';features=read(features_path);matching_path=OUT/'normalization-matching-results.json';matching=read(matching_path)
    assert features['status']=='all-auxiliary-core-content-matches-real-outputs' and len(features['rows'])==77 and features['fixed_queries_per_method']==644
    assert matching['feature_file_sha256']==sha(features_path) and len(matching['function_records'])==4508 and len(matching['module_records'])==56
    for row in features['rows']:
        actual=next(r for r in static['records'] if r['input_id']==row['input_id'] and r['method']==row['method'])
        aux=ROOT/row['auxiliary_path'];assert sha(aux)==row['auxiliary_sha256'] and core(aux.read_bytes())==core((ROOT/actual['path']).read_bytes())
        bodies=functions((ROOT/actual['canonical_path']).read_text(encoding='utf-8'));types=type_shapes(ROOT/actual['path'])
        assert [fingerprint(b,types) for b in bodies]==[f['fingerprint'] for f in row['functions']]
    for method in plan['methods']:
        expected={(item['id'],method['id'],origin) for item in plan['inputs'] for origin in features['origins'][item['id']]}
        observed={(r['input_id'],r['method'],r['origin_index']) for r in matching['function_records'] if r['method']==method['id']};assert expected==observed and len(observed)==644
    both=next(r for r in matching['summaries'] if r['method']=='both');assert both['outcomes']==dict(correct_unique=536,ambiguous_with_correct=104,unmatched=4)
    for r in matching['function_records']:
        if r['input_id'].startswith('published'):assert r['outcome']=='unmatched'
    helper=OUT/'normalization-helper-truth';h=read(helper/'checks.json');manifest=read(helper/'manifest.json')
    assert h['passed'] and h['cases']==698 and h['helper_calls']==2094 and all(r['matched'] for r in h['records'])
    assert not h['whole_miner_loaded'] and not h['mining_executed'] and h['wasm_sha256']==sha(helper/'isolated-xor.wasm')==manifest['wasm_sha256']
    assert h['cases_sha256']==sha(helper/'cases.json') and h['evaluator_sha256']==sha(ROOT/'scripts/check_followup_helper_truth.cjs')
    add('analysis-task','Evaluate a concrete function/module matching task, including ambiguity and lost provenance.',
        [features_path,matching_path,helper/'checks.json'],dict(function_queries=4508,module_queries=56,fixed_function_denominator=644,correct_unique_both=536,ambiguous_both=104,complex_unmatched=4,auxiliary_core_matches=77),
        ['Known-lineage exact syntax task; not semantic equivalence, human analysis time or detector performance. Retained-only rates are conditional.'])
    # Independent replay must cover every label with the same bounded execution setup.
    replay=OUT/'normalization-replays/172adcc0cd9b49aca166e490aaf62dfd';rs=read(replay/'status.json');rm=read(replay/'manifest.json')
    assert rs['status']=='replay-complete' and rs['labels']==77 and rs['output_checks']==2793 and len(rs['batches'])==11
    assert rs['manifest_sha256']==sha(replay/'manifest.json') and rm['replayer_sha256']==sha(ROOT/'scripts/replay_followup_normalization.py')
    replay_labels=set();replay_checks=0
    for entry in rs['batches']:
        run=ROOT/entry['run'];p,c=run_evidence(run);ap=run/'controlled-audit.json';a=read(ap)
        assert a['status']=='passed' and sha(ap)==entry['audit_sha256'] and sha(run/'outputs/controlled-checks.json')==entry['measurement_sha256']==a['measurement_sha256']
        for r in p['controlled']['artifacts']:assert r['id'] not in replay_labels;replay_labels.add(r['id'])
        replay_checks+=a['checks']
    assert replay_labels==labels and replay_checks==2793
    old=OUT/'normalization-replays/f3439623753041b0bb5538490a013b60';assert read(old/'status.json')['status']=='failed'
    assert sha(old/'replayer-source-v1.py')==read(old/'manifest.json')['replayer_sha256']
    assert 'FileNotFoundError' in (old/'webminerpoolhashcn-constsplit-stderr.txt').read_text(encoding='utf-8')
    add('reproducibility','Provide executable plans and validate a separate full replay while retaining failed attempts.',
        [replay/'status.json',replay/'manifest.json',old/'status.json',old/'replayer-source-v1.py',ROOT/'docs/followup-reproduction-20261016.md'],
        dict(replay_labels=77,replay_output_checks=2793,replay_batches=11,not_added_as_independent_samples=True),
        ['Exact cross-host runtime requires retaining the fixed image; Dockerfile apt packages are not all version-pinned.'])
    primary=read(OUT/'prior-method-audit.json');assert primary['status']=='saved-primary-blobs-match'
    for r in primary['files']:
        p=ROOT/r['path'];data=p.read_bytes();assert sha(p)==r['sha256']
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==r['git_blob_sha1']
    add('prior-research','Respect primary sources, established methods and the limits of historical reproduction.',
        [OUT/'prior-method-audit.json',ROOT/'docs/followup-research-report-20261016.md'],
        dict(saved_primary_blobs=3,binaryen_O3_included=True,historical_commit_distinguished=True),
        ['Thesis chapter not fully inspected; no novelty claim or claim to reproduce the historical compiler commit.'])
    # Rendered figures were manually inspected; bind that review to the exact current pixels and source data.
    figures=0
    for generation_name,review_name,count in [('confirmatory-generation.json','confirmatory-visual-review.json',3),('normalization-generation.json','normalization-visual-review.json',2)]:
        gp=OUT/'figures'/generation_name;rp=OUT/'figures'/review_name;g=read(gp);r=read(rp)
        assert r['generation_sha256']==sha(gp) and len(r['images'])==count
        for image in r['images']:
            name=image.get('path',image.get('file'));assert sha(OUT/'figures'/name)==image['sha256'] and image['status']=='visually-reviewed'
        for image in g['files']:assert sha(OUT/'figures'/image['path'])==image['sha256']
        figures+=count;evidence_files.update([gp,rp])
    assert figures==5
    docs=['followup-research-report-20261016.md','followup-performance-results-20261016.md','followup-normalization-results-20261016.md','followup-reproduction-20261016.md','paper-followup-reflection-20261016.md','followup-evaluation-progress-20261016.md']
    for name in docs:assert len((ROOT/'docs'/name).read_text(encoding='utf-8'))>500
    paper_proposal=(ROOT/'docs/paper-followup-reflection-20261016.md').read_text(encoding='utf-8');assert 'アブストラクト案' in paper_proposal and 'RQ2' in paper_proposal and '2,793' in paper_proposal
    add('deliverables','Deliver reports, reviewed figures, reproducible records and a concrete paper reflection proposal.',
        [ROOT/'docs'/name for name in docs]+[OUT/'figures/confirmatory-visual-review.json',OUT/'figures/normalization-visual-review.json'],
        dict(reports=len(docs),reviewed_figures=5,paper_body_preserved=True,abstract_and_conclusion_proposals=True),
        ['Proposal is delivered separately; publishing/rewriting the current paper was not required.'])
    # Existence of preserved early failures is part of the record, not a passing measurement.
    failures=[OUT/'runs/input-diagnostic-2f43d8c5eaf649ac9011e28a1260ff97/failure.json',OUT/'controlled-adapter-first-failure.json',
        ROOT/recovery['preserved_failure_stderr'],oom/'failure.json',old/'webminerpoolhashcn-constsplit-stderr.txt']
    for p in failures:assert p.is_file() and p.stat().st_size>0
    add('failure-history','Retain failed starts, adapter/summary mistakes, OOM and path-length failures.',failures,dict(preserved_failure_records=len(failures),pilot_compiler_deviation_preserved=True))
    result=dict(status='all-requirements-proved-with-stated-scope',requirements=requirements,
        evidence_hashes=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=sha(p)) for p in sorted(evidence_files)],
        audit_script_sha256=sha(Path(__file__)),wasm_executed_by_this_audit=False,
        app_goal_completion='Pending explicit update_goal call after reviewing this audit.',
        no_remaining_required_research_work=True)
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],requirements=len(requirements),evidence_files=len(evidence_files),reviewed_figures=figures),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
