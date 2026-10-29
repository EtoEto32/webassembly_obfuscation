"""Aggregate only three completed/audited sessions; keep every preplanned contrast."""
import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def interval_from_sessions(rows):
    grouped=defaultdict(list)
    for r in rows:grouped[r['session']].append(math.log(r['ratio']))
    assert set(grouped)=={1,2,3} and all(len(v)==2 for v in grouped.values())
    means=[statistics.mean(grouped[i]) for i in [1,2,3]]
    estimate=statistics.mean(means);se=statistics.stdev(means)/math.sqrt(3)
    # Exact inversion of Student t with df=2 at p=.975; NIST table rounds to 4.303.
    tail=2*.975-1;critical=math.sqrt(2)*tail/math.sqrt(1-tail*tail)
    assert round(critical,3)==4.303
    return dict(geometric_mean_ratio=math.exp(estimate),
        exploratory_session_t_interval_95=[math.exp(estimate-critical*se),math.exp(estimate+critical*se)],
        session_geometric_ratios=[math.exp(m) for m in means],
        interval_units='Three session mean log-ratios, two repetitions per session; df=2.',
        assumptions='Approximate independent normally distributed session mean log-ratios. Three consecutive sessions cannot validate these assumptions; interval is exploratory, not a population or equivalence claim.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execution',type=Path,required=True);args=parser.parse_args()
    status_path=args.execution.resolve()/'status.json';execution=json.loads(status_path.read_text(encoding='utf-8'))
    assert execution['status']=='stage-complete' and len(execution['sessions'])==3
    manifest_path=OUT/'confirmatory-plans.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    rows=[];samples=[];sources=[];cpu_models=set();artifacts={};group_specs={};aa=[];reference_pairs=[];native=[]
    for item in execution['sessions']:
        assert item['audit']=='passed';session=item['session']
        run=ROOT/item['run'].replace('\\','/')
        plan_path=run/'inputs/plan.json';plan=json.loads(plan_path.read_text(encoding='utf-8'))
        expected=manifest['plans'][session-1]
        assert sha(plan_path)==expected['sha256']
        audit_path=run/'confirmatory-audit.json';audit=json.loads(audit_path.read_text(encoding='utf-8'))
        raw_path=run/'outputs/runtime.json';raw=json.loads(raw_path.read_text(encoding='utf-8'))
        assert audit['status']=='passed' and audit['session']==session and audit['plan_sha256']==sha(plan_path)
        assert audit['measurement_sha256']==sha(raw_path) and raw['status']=='complete'
        assert len(raw['samples'])==expected['blocks']==audit['samples']
        cpu_models.add(raw['cpu_model']);rows.extend(audit['comparisons']);samples.extend(raw['samples'])
        # Same V8 trace grammar as the pilot audit. Allocation bytes are NOT code bytes.
        compilation=re.compile(r'Compiled function \S+#(\d+) using (\w+), took (\d+) ms and (\d+)(?: / \d+ max/total)? bytes; bodysize (\d+) codesize (\d+)')
        for check in audit['compiler_checks']:
            sample=raw['samples'][check['sequence']]
            trace_path=run/'outputs'/(str(check['sequence']).zfill(3)+'-stdout.txt')
            assert sha(trace_path)==check['trace_sha256']
            text=trace_path.read_text(encoding='utf-8');records=compilation.findall(text)
            assert records and len(records)==sum(line.startswith('Compiled function ') for line in text.splitlines())
            assert {r[1] for r in records}=={check['compiler']}
            native.append(dict(session=session,sequence=check['sequence'],mode=sample['mode'],artifact_id=sample['artifact_id'],
                compilation_records=len(records),distinct_function_indices=len({int(r[0]) for r in records}),
                reported_body_bytes=sum(int(r[4]) for r in records),reported_code_bytes=sum(int(r[5]) for r in records),
                trace_sha256=check['trace_sha256']))
        aa.extend(audit['AA_comparisons'])
        for contrast in audit['comparisons']:
            sequence=contrast['sequence'];left,right=raw['samples'][sequence-1],raw['samples'][sequence+1]
            assert left['artifact_id']==right['artifact_id']
            reference_pairs.append(dict(session=session,mode=contrast['mode'],group=contrast['group'],
                variant_id=contrast['artifact_id'],left_sequence=left['sequence'],right_sequence=right['sequence'],
                left_hps=left['hashes_per_second'],right_hps=right['hashes_per_second'],
                right_over_left=right['hashes_per_second']/left['hashes_per_second']))
        for a in plan['runtime']['artifacts']:
            if a['id'] in artifacts:assert artifacts[a['id']]==a
            artifacts[a['id']]=a
        for g in plan['runtime']['groups']:group_specs[g['id']]=g
        sources.append(dict(session=session,run=str(run.relative_to(ROOT)).replace('\\','/'),
            audit_sha256=sha(audit_path),measurement_sha256=sha(raw_path),plan_sha256=sha(plan_path)))
    assert len(cpu_models)==1 and len(samples)==manifest['total_blocks']==272
    comparisons=defaultdict(list)
    for r in rows:comparisons[(r['mode'],r['group'],r['artifact_id'])].append(r)
    wanted={(mode['id'],g['id'],identifier) for mode in manifest['modes'] for g in group_specs.values() for identifier in g['variants']}
    assert set(comparisons)==wanted and len(rows)==108
    summaries=[]
    for key,records in sorted(comparisons.items()):
        assert len(records)==6 and {r['repetition'] for r in records}==set(range(1,7))
        ordered=sorted(records,key=lambda r:r['repetition']);ratios=[r['ratio'] for r in ordered]
        summaries.append(dict(mode=key[0],group=key[1],artifact_id=key[2],repetitions=6,
            median_ratio=statistics.median(ratios),minimum_ratio=min(ratios),maximum_ratio=max(ratios),
            ratios_by_repetition=ratios,median_hps=statistics.median(r['variant_hps'] for r in records),
            median_interpolated_reference_hps=statistics.median(r['interpolated_reference_hps'] for r in records),
            maximum_reference_gap_seconds=max(r['reference_gap_seconds'] for r in records),
            **interval_from_sessions(records)))
    telemetry=[]
    for s in samples:
        before=s['cgroup_before']['values'] if s['cgroup_before'] else {}
        after=s['cgroup_after']['values'] if s['cgroup_after'] else {}
        throttled=None
        if 'throttled_usec' in before:throttled=(after['throttled_usec']-before['throttled_usec'])/1000
        elif 'throttled_time' in before:throttled=(after['throttled_time']-before['throttled_time'])/10**6
        bin_rates=[b['count']*1000/b['elapsed_ms'] for b in s['bins']]
        telemetry.append(dict(session=s['session'],sequence=s['sequence'],artifact_id=s['artifact_id'],mode=s['mode'],
            elapsed_ms=s['elapsed_ms'],cpu_fraction=(s['cpu_time_us']['user']+s['cpu_time_us']['system'])/1000/s['elapsed_ms'],
            throttled_ms=throttled,full_bins=len(bin_rates),
            bin_hps_minimum=min(bin_rates),bin_hps_maximum=max(bin_rates),
            bin_hps_cv=statistics.stdev(bin_rates)/statistics.mean(bin_rates) if len(bin_rates)>1 else None))
    native_groups=defaultdict(list)
    for record in native:native_groups[record['mode'],record['artifact_id']].append(record)
    native_summaries=[]
    for (mode,identifier),records in sorted(native_groups.items()):
        native_summaries.append(dict(mode=mode,artifact_id=identifier,observed_blocks=len(records),
            code_bytes_minimum=min(r['reported_code_bytes'] for r in records),
            code_bytes_maximum=max(r['reported_code_bytes'] for r in records),
            compilation_records_minimum=min(r['compilation_records'] for r in records),
            compilation_records_maximum=max(r['compilation_records'] for r in records),
            distinct_function_indices_minimum=min(r['distinct_function_indices'] for r in records),
            distinct_function_indices_maximum=max(r['distinct_function_indices'] for r in records)))
    result=dict(status='all-three-sessions-audited',sources=sources,cpu_model=next(iter(cpu_models)),
        unique_sha256=len({a['sha256'] for a in artifacts.values()}),artifact_labels=len(artifacts),
        timed_blocks=len(samples),paired_contrasts=len(rows),summaries=summaries,telemetry=telemetry,
        AA_comparisons=aa,baseline_reference_pairs=reference_pairs,
        baseline_variation_scope='Descriptive A/A and before/after reference ratios. References may be shared between adjacent contrasts; these are not independent samples or a noise correction. Bin rates omit the final incomplete bin and are descriptive only.',
        compiled_code_blocks=native,compiled_code_summaries=native_summaries,
        compiled_code_scope='Sums of V8-reported codesize from all compilation records in each fresh block; eager compilation includes unexecuted functions. Not compiler allocation bytes, resident memory, native instruction counts or hot-path execution counts. Preserve ranges rather than assume invariant sizes.',
        baseline_aggregation='Near references interpolate at timed-block midpoints; every planned block retained.',
        interval_method='Exploratory t interval on three session mean log-ratios, df=2; conditional on approximate normality and session independence.',
        interval_multiplicity='Pointwise intervals for all 18 predefined contrasts; no multiplicity adjustment or simultaneous-coverage claim. Do not interpret exclusion of one as a confirmatory significance test.',
        interval_references=['https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm',
            'https://www.itl.nist.gov/div898/handbook/eda/section3/eda3672.htm'],
        no_equivalence_claim=True,no_posthoc_exclusions=True,no_population_inference=True,
        compiler_modes=[m['id'] for m in manifest['modes']],
        limits=['Three consecutive sessions do not validate independence or population representativeness.',
            'Shared CryptoNight lineage; transformations and manual helper restoration are distinct comparisons.',
            'Compiler tracing and nonexclusive guest CPU placement limit interpretation of small differences.',
            'Compiler-event checks cover Wasm only; JavaScript host JIT and all other runtime activity are not traced or excluded by this audit.',
            'Manual helper restoration does not establish an automatic normalization algorithm.'],
        summary_script_sha256=sha(Path(__file__)),execution_status_sha256=sha(status_path))
    destination=OUT/'confirmatory-summary.json'
    if destination.exists():raise RuntimeError('Preserve existing summary')
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    columns=['mode','group','artifact_id','repetitions','median_hps','median_ratio','minimum_ratio','maximum_ratio','geometric_mean_ratio','exploratory_session_t_interval_95','ratios_by_repetition']
    with (OUT/'confirmatory-summary.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=columns);writer.writeheader()
        for s in summaries:writer.writerow({k:s[k] for k in columns})
    print(json.dumps(dict(status=result['status'],timed_blocks=len(samples),paired_contrasts=len(rows),summaries=summaries),indent=2))


if __name__=='__main__':main()
