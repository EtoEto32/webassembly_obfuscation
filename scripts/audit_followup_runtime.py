"""Audit completed pilot before descriptive comparisons; never run Wasm."""
import argparse
import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def midpoint(sample):
    return datetime.fromisoformat(sample['started_utc'].replace('Z','+00:00')).timestamp()+sample['elapsed_ms']/2000


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run',type=Path);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT)
    plan_path=run/'inputs/plan.json';plan=json.loads(plan_path.read_text(encoding='utf-8'))
    raw_path=run/'outputs/runtime.json';report=json.loads(raw_path.read_text(encoding='utf-8'))
    completion=json.loads((run/'completion.json').read_text(encoding='utf-8'))
    inspect=json.loads((run/'container-inspect.json').read_text(encoding='utf-8'))
    assert report['status']=='complete' and completion['exit_code']==0 and completion['state']['ExitCode']==0
    assert not completion['state']['OOMKilled'] and not completion['state']['Running']
    assert report['plan_sha256']==sha(plan_path)
    assert len(report['samples'])==len(plan['runtime']['schedule'])
    for a in plan['assets']:
        assert sha(run/'inputs'/a['name'])==a['sha256']
        assert sha(ROOT/a['path'])==a['sha256']
    host=inspect['HostConfig'];mounts={m['Destination']:m for m in inspect['Mounts']}
    assert inspect['Image']==plan['image'] and host['NetworkMode']=='none' and host['CpusetCpus']=='0'
    assert host['NanoCpus']==10**9 and host['Memory']==1024**3 and host['MemorySwap']==1024**3
    assert host['PidsLimit']==64 and host['ReadonlyRootfs'] and inspect['Config']['User']=='10001:10001'
    assert 'ALL' in host['CapDrop'] and any(s.startswith('no-new-privileges') for s in host['SecurityOpt'])
    assert not mounts['/inputs']['RW'] and mounts['/outputs']['RW']
    groups=defaultdict(list);tiers=[];summaries=defaultdict(list);last_end=None;mode_deviations=[]
    # TurboFan reports peak/total compiler allocation; Liftoff reports one allocation.
    pattern=re.compile(r'Compiled function \S+#(\d+) using (\w+), took (\d+) ms and (\d+)(?: / \d+ max/total)? bytes; bodysize (\d+) codesize (\d+)')
    for expected,sample in zip(plan['runtime']['schedule'],report['samples']):
        assert all(sample[k]==v for k,v in expected.items())
        artifact=next(a for a in plan['runtime']['artifacts'] if a['id']==sample['artifact_id'])
        assert sample['sha256']==artifact['sha256']
        assert sample['elapsed_ms']>=plan['runtime']['block_seconds']*1000 and sample['count']>0
        assert sample['warmup_ms']>=plan['runtime']['warmup_seconds']*1000 and sample['warmup_count']>0
        assert abs(sample['hashes_per_second']-sample['count']*1000/sample['elapsed_ms'])<1e-9
        assert sample['final_output']==sample['final_expected'] and sample['final_nonce_unchanged']
        vectors=[v for v in plan['public_vectors'] if artifact['family']!='xmr-wasm' or bytes.fromhex(v['hex'])[0]<7]
        for checks in [sample['pre_checks'],sample['post_checks']]:
            assert len(checks)==len(vectors)
            assert all(c['id']==v['id'] and c['actual']==c['expected']==v['expected'] and c['nonce_unchanged'] for c,v in zip(checks,vectors))
        assert all(len(bytes.fromhex(v['hex']))==76 for v in vectors)
        start=datetime.fromisoformat(sample['started_utc'].replace('Z','+00:00')).timestamp()
        end=datetime.fromisoformat(sample['finished_utc'].replace('Z','+00:00')).timestamp()
        assert end-start+.01>=sample['elapsed_ms']/1000
        if last_end is not None:
            assert start>=last_end
        last_end=end
        assert sample['cpu_time_us']['user']>=0 and sample['cpu_time_us']['system']>=0
        assert sample['affinity_status']==['Cpus_allowed_list:\t0']
        if sample['cgroup_before'] and sample['cgroup_after']:
            for k,value in sample['cgroup_before']['values'].items():
                assert sample['cgroup_after']['values'][k]>=value
        trace_path=run/'outputs'/(str(sample['sequence']).zfill(3)+'-stdout.txt')
        trace=trace_path.read_text(encoding='utf-8')
        matches=pattern.findall(trace);assert matches
        types=Counter(row[1] for row in matches)
        if sample['mode']=='liftoff':
            if set(types)!={'Liftoff'}:
                mode_deviations.append(dict(sequence=sample['sequence'],requested_mode='liftoff-only',observed_compilation_counts=dict(types)))
        if sample['mode']=='turbofan':
            if set(types)!={'TurboFan'}:
                mode_deviations.append(dict(sequence=sample['sequence'],requested_mode='turbofan-only',observed_compilation_counts=dict(types)))
        mode=next(m for m in plan['runtime']['modes'] if m['id']==sample['mode'])
        assert sample['flags']==mode['flags']+['--trace-wasm-compilation-times']
        tiers.append(dict(sequence=sample['sequence'],mode=sample['mode'],artifact_id=sample['artifact_id'],
            compilation_counts=dict(types),trace_sha256=sha(trace_path),
            generated_code_bytes_by_tier={tier:sum(int(row[5]) for row in matches if row[1]==tier) for tier in types}))
        groups[(sample['repetition'],sample['mode'],sample['family'])].append(sample)
        summaries[(sample['mode'],sample['family'],sample['artifact_id'])].append(sample['hashes_per_second'])
    comparisons=[];aa=[]
    for key,group in groups.items():
        assert len(group)==6 and group[0]['role']=='AA-first' and group[1]['role']=='AA-second'
        aa.append(dict(repetition=key[0],mode=key[1],family=key[2],ratio=group[1]['hashes_per_second']/group[0]['hashes_per_second']))
        for i in [2,4]:
            left,variant,right=group[i-1:i+2]
            assert variant['role']=='variant' and right['role']=='bracket-reference'
            weight=(midpoint(variant)-midpoint(left))/(midpoint(right)-midpoint(left));assert 0<weight<1
            reference=left['hashes_per_second']*(1-weight)+right['hashes_per_second']*weight
            comparisons.append(dict(repetition=key[0],mode=key[1],family=key[2],artifact_id=variant['artifact_id'],
                ratio=variant['hashes_per_second']/reference,reference_hps_interpolated=reference,
                left_reference_hps=left['hashes_per_second'],right_reference_hps=right['hashes_per_second'],
                reference_midpoint_gap_seconds=midpoint(right)-midpoint(left)))
    result=dict(status='passed' if not mode_deviations else 'measurement-checks-passed-with-compiler-mode-deviation',
        compiler_mode_validation='passed' if not mode_deviations else 'failed',compiler_mode_deviations=mode_deviations,
        plan_sha256=sha(plan_path),measurement_sha256=sha(raw_path),
        audited_run=str(run.relative_to(ROOT)).replace('\\','/'),samples=len(report['samples']),
        rate_summaries=[dict(mode=k[0],family=k[1],artifact_id=k[2],n=len(v),median_hps=statistics.median(v),minimum_hps=min(v),maximum_hps=max(v)) for k,v in summaries.items()],
        bracket_comparisons=comparisons,AA_comparisons=aa,compilation_checks=tiers,
        nonce_check_scope='The xmr wrapper checks nonce bytes. The SWAMPED pilot sets its nonce indicator to true without inspecting input memory; do not interpret that field as an independent SWAMPED nonce check.',
        compilation_log_scope='Entire fresh child process: initialization, validation, warmup, measurement and postchecks. Logs do not timestamp per-function tier transitions within the timed interval.',
        limitations=['Pilot only, two session rounds, no powered equivalence or significance claim.',
            'Interpolation assumes smooth local drift and cannot remove arbitrary interference.',
            'Compiler tracing enabled in every condition; do not claim trace-free production performance.',
            'CPU time is process-wide and can include compilation threads.',
            'Guest CPU affinity is not exclusive host physical-core allocation.',
            'Published xmr binaries still have historical build differences.'])
    destination=run/'pilot-audit.json'
    if destination.exists():
        raise RuntimeError('Preserve existing audit')
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],samples=result['samples'],AA_ratios=[r['ratio'] for r in aa],rates=result['rate_summaries']),indent=2))


if __name__=='__main__':
    main()
