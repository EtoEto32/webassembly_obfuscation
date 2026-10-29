"""Strict per-session audit for the corrected fixed-compiler comparisons."""
import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def midpoint(s):return datetime.fromisoformat(s['started_utc'].replace('Z','+00:00')).timestamp()+s['elapsed_ms']/2000


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run',type=Path);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT)
    pp=run/'inputs/plan.json';plan=json.loads(pp.read_text(encoding='utf-8'))
    rp=run/'outputs/runtime.json';data=json.loads(rp.read_text(encoding='utf-8'))
    completed=json.loads((run/'completion.json').read_text(encoding='utf-8'))
    inspected=json.loads((run/'container-inspect.json').read_text(encoding='utf-8'))
    assert plan['runtime']['stage']=='controlled-confirmatory' and data['status']=='complete'
    assert completed['exit_code']==0 and completed['state']['ExitCode']==0 and not completed['state']['OOMKilled']
    assert data['plan_sha256']==sha(pp) and len(data['samples'])==len(plan['runtime']['schedule'])
    for a in plan['assets']:
        assert sha(run/'inputs'/a['name'])==a['sha256'] and sha(ROOT/a['path'])==a['sha256']
    host=inspected['HostConfig'];mounts={m['Destination']:m for m in inspected['Mounts']}
    assert inspected['Image']==plan['image'] and host['NetworkMode']=='none' and host['CpusetCpus']=='0'
    assert host['NanoCpus']==10**9 and host['Memory']==1024**3 and host['MemorySwap']==1024**3
    assert host['PidsLimit']==64 and host['ReadonlyRootfs'] and inspected['Config']['User']=='10001:10001'
    assert 'ALL' in host['CapDrop'] and any(s.startswith('no-new-privileges') for s in host['SecurityOpt'])
    assert not mounts['/inputs']['RW'] and mounts['/outputs']['RW']
    samples=data['samples'];comparisons=[];aa=[];compilers=[];last_finished=None
    for expected,s in zip(plan['runtime']['schedule'],samples):
        assert all(s[k]==v for k,v in expected.items())
        artifact=next(a for a in plan['runtime']['artifacts'] if a['id']==s['artifact_id'])
        assert s['sha256']==artifact['sha256'] and s['elapsed_ms']>=30000 and s['warmup_ms']>=5000
        assert s['count']>0 and s['warmup_count']>0 and abs(s['hashes_per_second']-s['count']*1000/s['elapsed_ms'])<1e-9
        assert s['final_output']==s['final_expected'] and s['final_nonce_unchanged']
        vectors=[v for v in plan['public_vectors'] if artifact['family']!='xmr-wasm' or bytes.fromhex(v['hex'])[0]<7]
        assert all(len(bytes.fromhex(v['hex']))==76 for v in vectors)
        assert s['final_expected']==vectors[(s['count']-1)%len(vectors)]['expected']
        began=datetime.fromisoformat(s['started_utc'].replace('Z','+00:00')).timestamp()
        finished=datetime.fromisoformat(s['finished_utc'].replace('Z','+00:00')).timestamp()
        assert finished-began+.01>=s['elapsed_ms']/1000
        if last_finished is not None:assert began>=last_finished
        last_finished=finished
        assert all(b['count']>0 and b['elapsed_ms']>=1000 for b in s['bins'])
        assert sum(b['count'] for b in s['bins'])<=s['count']
        assert sum(b['elapsed_ms'] for b in s['bins'])<=s['elapsed_ms']+.01
        for checks in [s['pre_checks'],s['post_checks']]:
            assert len(checks)==len(vectors)
            assert all(c['id']==v['id'] and c['actual']==c['expected']==v['expected'] and c['nonce_unchanged'] for c,v in zip(checks,vectors))
        assert s['nonce_check_kind']==('not-applicable-string-API' if artifact['family']=='webminerpoolhashcn' else 'input-memory-bytes')
        mode=next(m for m in plan['runtime']['modes'] if m['id']==s['mode']);assert s['flags']==mode['flags']+['--trace-wasm-compilation-times']
        trace_path=run/'outputs'/(str(s['sequence']).zfill(3)+'-stdout.txt');trace=trace_path.read_text(encoding='utf-8')
        types=set(re.findall(r'using (Liftoff|TurboFan),',trace));assert types==({'Liftoff'} if s['mode']=='liftoff' else {'TurboFan'}),types
        lines=trace.splitlines();begin=next(i for i,l in enumerate(lines) if l.startswith('FOLLOWUP_PHASE timed-start'))
        end=next(i for i,l in enumerate(lines) if l.startswith('FOLLOWUP_PHASE timed-end'));assert end>begin
        during=[line for line in lines[begin+1:end] if line.startswith('Compiled function ')]
        assert not during,'Compilation inside fixed-tier timed interval'
        assert s['affinity_status']==['Cpus_allowed_list:\t0']
        assert s['cpu_time_us']['user']>=0 and s['cpu_time_us']['system']>=0
        if s['cgroup_before'] and s['cgroup_after']:
            assert all(s['cgroup_after']['values'][k]>=v for k,v in s['cgroup_before']['values'].items())
        compilers.append(dict(sequence=s['sequence'],compiler=next(iter(types)),timed_compilation_events=0,trace_sha256=sha(trace_path)))
        if s['role']=='AA-second':
            left=samples[s['sequence']-1];assert left['artifact_id']==s['artifact_id'] and left['group']==s['group']
            aa.append(dict(session=s['session'],repetition=s['repetition'],mode=s['mode'],group=s['group'],ratio=s['hashes_per_second']/left['hashes_per_second']))
        if s['role']=='variant':
            i=s['sequence'];left,right=samples[i-1],samples[i+1]
            group=next(g for g in plan['runtime']['groups'] if g['id']==s['group'])
            assert left['artifact_id']==right['artifact_id']==group['baseline']
            assert left['group']==right['group']==s['group'] and right['role']=='bracket-reference'
            weight=(midpoint(s)-midpoint(left))/(midpoint(right)-midpoint(left));assert 0<weight<1
            reference=left['hashes_per_second']*(1-weight)+right['hashes_per_second']*weight
            comparisons.append(dict(session=s['session'],repetition=s['repetition'],mode=s['mode'],group=s['group'],
                artifact_id=s['artifact_id'],variant_hps=s['hashes_per_second'],interpolated_reference_hps=reference,
                ratio=s['hashes_per_second']/reference,reference_gap_seconds=midpoint(right)-midpoint(left),
                sequence=s['sequence']))
    result=dict(status='passed',session=plan['runtime']['session'],plan_sha256=sha(pp),measurement_sha256=sha(rp),
        audited_run=str(run.relative_to(ROOT)).replace('\\','/'),samples=len(samples),comparisons=comparisons,AA_comparisons=aa,
        compiler_checks=compilers,auditor_sha256=sha(Path(__file__)),
        limits=['Finite implementation-conditional comparisons; shared code lineage remains.',
            'Linear baseline interpolation cannot remove arbitrary transient noise.',
            'Fresh-process startup and output checks are excluded from the timed interval.',
            'Compiler tracing remains enabled; guest CPU0 is not exclusive physical-core ownership.'])
    destination=run/'confirmatory-audit.json';assert not destination.exists()
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='passed',session=result['session'],samples=len(samples),comparisons=len(comparisons))))


if __name__=='__main__':main()
