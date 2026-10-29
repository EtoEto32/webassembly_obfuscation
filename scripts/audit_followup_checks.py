"""Audit path counters or controlled outputs against the executed frozen plan."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['paths','controlled']);parser.add_argument('run',type=Path);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT)
    plan_path=run/'inputs/plan.json';plan=json.loads(plan_path.read_text(encoding='utf-8'))
    raw_path=run/'outputs'/('paths.json' if args.kind=='paths' else 'controlled-checks.json')
    data=json.loads(raw_path.read_text(encoding='utf-8'))
    completion=json.loads((run/'completion.json').read_text(encoding='utf-8'))
    inspect=json.loads((run/'container-inspect.json').read_text(encoding='utf-8'))
    assert completion['exit_code']==0 and completion['state']['ExitCode']==0 and not completion['state']['OOMKilled']
    assert data['status']=='complete' and data['plan_sha256']==sha(plan_path)
    for a in plan['assets']:
        assert sha(run/'inputs'/a['name'])==a['sha256'] and sha(ROOT/a['path'])==a['sha256']
    host=inspect['HostConfig'];mounts={m['Destination']:m for m in inspect['Mounts']}
    assert inspect['Image']==plan['image'] and host['NetworkMode']=='none' and host['CpusetCpus']=='0'
    assert host['NanoCpus']==10**9 and host['Memory']==1024**3 and host['MemorySwap']==1024**3
    assert host['PidsLimit']==64 and host['ReadonlyRootfs'] and inspect['Config']['User']=='10001:10001'
    assert 'ALL' in host['CapDrop'] and any(s.startswith('no-new-privileges') for s in host['SecurityOpt'])
    assert not mounts['/inputs']['RW'] and mounts['/outputs']['RW']
    result=dict(status='passed',kind=args.kind,plan_sha256=sha(plan_path),measurement_sha256=sha(raw_path),
        audited_run=str(run.relative_to(ROOT)).replace('\\','/'))
    if args.kind=='paths':
        expected=plan['path_diagnostic'];vectors={v['id']:v for v in expected['vectors']}
        for field,artifacts in [('counts',expected['artifacts']),('ablations',expected['ablations'])]:
            assert Counter((r['id'],r['vector_id']) for r in data[field])==Counter((a['id'],v) for a in artifacts for v in vectors)
            for row in data[field]:
                assert row['actual']==row['expected']==vectors[row['vector_id']]['expected'] and row['nonce_unchanged']
        for row in data['counts']:
            assert row['hash_deltas']['hash']=='1'
            snapshots=row['snapshots']
            for name,delta in row['hash_deltas'].items():
                assert int(delta)==int(snapshots['after_hash'][name])-int(snapshots['after_allocate'][name])>=0
                assert int(snapshots['after_free'][name])>=int(snapshots['after_hash'][name])
        result.update(counted_checks=len(data['counts']),ablation_output_checks=len(data['ablations']),
            per_hash_counts=[dict(id=r['id'],vector_id=r['vector_id'],counts=r['hash_deltas']) for r in data['counts']],
            interpretation='Function-entry counts only; do not infer instruction counts or time shares. Manual helper ablations are diagnostic controls, not an automatic normalization algorithm.')
    else:
        assert len(data['reference_public'])==5
        assert all(r['actual']==r['expected'] for r in data['reference_public'])
        assert len(data['additional_vectors'])==len(plan['controlled']['additional_vectors'])==8
        vectors={v['id']:v for v in plan['public_vectors']+data['additional_vectors']}
        wanted=[]
        for artifact in plan['controlled']['artifacts']:
            for mode in plan['controlled']['modes']:
                wanted.extend((artifact['id'],mode,v['id']) for v in vectors.values()
                    if artifact['family']!='xmr-wasm' or bytes.fromhex(v['hex'])[0]<7)
        assert Counter((r['artifact_id'],r['mode'],r['vector_id']) for r in data['checks'])==Counter(wanted)
        for row in data['checks']:
            assert row['actual']==row['expected']==vectors[row['vector_id']]['expected']
            assert len(bytes.fromhex(vectors[row['vector_id']]['hex']))==76
        result.update(checks=len(data['checks']),artifacts=len(plan['controlled']['artifacts']),
            per_artifact=dict(Counter(r['artifact_id'] for r in data['checks'])),
            public_checks=sum(r['vector_id'].startswith('xmrig-') for r in data['checks']),
            reference_derived_checks=sum(r['vector_id'].startswith('controlled-') for r in data['checks']),
            interpretation='Three existing implementations with shared CryptoNight lineage; finite input/historical-state checks, not whole-module equivalence.')
    destination=run/(args.kind+'-audit.json')
    if destination.exists():
        raise RuntimeError('Preserve previous audit')
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
