"""Audit frozen assets, isolation, output counts and canonical-input comparisons."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run',type=Path);args=parser.parse_args()
    run=args.run.resolve();assert run.is_relative_to(ROOT)
    plan_path=run/'inputs/plan.json';plan=json.loads(plan_path.read_text(encoding='utf-8'))
    report_path=run/'outputs/input-diagnostic.json';report=json.loads(report_path.read_text(encoding='utf-8'))
    completion=json.loads((run/'completion.json').read_text(encoding='utf-8'))
    inspection=json.loads((run/'container-inspect.json').read_text(encoding='utf-8'))
    assert report['status']=='complete' and completion['exit_code']==0
    assert completion['state']['ExitCode']==0 and not completion['state']['OOMKilled'] and not completion['state']['Running']
    assert report['plan_sha256']==sha(plan_path)
    for a in plan['assets']:
        assert sha(run/'inputs'/a['name'])==a['sha256']
        assert sha(ROOT/a['path'])==a['sha256']
    host=inspection['HostConfig'];mounts={m['Destination']:m for m in inspection['Mounts']}
    assert host['NetworkMode']=='none' and host['NanoCpus']==10**9 and host['CpusetCpus']=='0'
    assert host['Memory']==1024**3 and host['MemorySwap']==1024**3 and host['PidsLimit']==64
    assert host['ReadonlyRootfs'] and inspection['Config']['User']=='10001:10001'
    assert 'ALL' in host['CapDrop'] and any(s.startswith('no-new-privileges') for s in host['SecurityOpt'])
    assert not mounts['/inputs']['RW'] and mounts['/outputs']['RW'] and inspection['Image']==plan['image']
    assert len(report['public_checks'])==15 and len(report['length_argument_checks'])==27
    assert len(report['history_checks'])==81 and len(report['tail_checks'])==6 and len(report['boundary_checks'])==6
    assert Counter((r['case_id'],r['id']) for r in report['public_checks'])==Counter((c['id'],v['id']) for c in plan['cases'] for v in plan['public_vectors'])
    assert all(r['actual']==r['expected'] for r in report['public_checks'])
    assert all(r['actual']==plan['public_vectors'][0]['expected'] for r in report['length_argument_checks'])
    expected_length_pairs=Counter((c['id'],n) for c in plan['cases'] for n in plan['input_diagnostic']['length_arguments'])
    assert Counter((r['case_id'],r['argument']) for r in report['length_argument_checks'])==expected_length_pairs
    histories=defaultdict(set);by_prefix=defaultdict(set)
    for r in report['history_checks']:
        assert len(bytes.fromhex(r['effective_input_76_hex']))==76 and r['actual']==r['canonical_expected']
        by_prefix[r['effective_input_76_hex']].add(r['actual'])
        histories[(r['length'],r['fill'])].add(r['actual'])
    assert all(len(values)==1 for values in by_prefix.values())
    for length in [1,8,32]:
        assert len(histories[(length,'retain')])==3
        assert len(histories[(length,'zero')])==1 and len(histories[(length,'ff')])==1
    for r in report['boundary_checks']:
        assert r['matches_original']==(r['changed_byte']==76)
    assert len({r['actual'] for r in report['boundary_checks'] if r['changed_byte']==75})==1
    refs=report['reference_checks'];assert all(r['actual']==r['expected'] for r in refs)
    reference_prefixes={r['hex'] for r in refs if r['family']=='webminerpoolhashcn' and r['kind']=='effective-76-byte-buffer'}
    assert set(by_prefix).issubset(reference_prefixes) and len(reference_prefixes)==14
    assert all(r['matches_public'] for r in report['tail_checks'])
    result=dict(status='passed',plan_sha256=sha(plan_path),measurement_sha256=sha(report_path),
        audited_run=str(run.relative_to(ROOT)).replace('\\','/'),
        target_public_checks=15,length_argument_checks=27,history_checks=81,tail_checks=6,boundary_checks=6,
        reference_public_checks=sum(r['kind']=='public' for r in refs),
        reference_effective_input_checks=sum(r['kind']=='effective-76-byte-buffer' for r in refs),
        unique_effective_inputs_with_webminerpool_reference=14,
        observed_contract='The existing SWAMPED entry processes the first 76 buffer bytes regardless of its fourth argument. Short-input history is reproduced by effective-buffer contents.',
        impact='Published 76-byte vector checks remain valid for the three tested binaries. Earlier extra short/long inputs were differential probes of this fixed-width entry, not independent arbitrary-length CryptoNight validation.',
        limitations=['Reference implementations share algorithm/source lineage; agreement is not a formal proof.',
            'No claim about every SWAMPED binary or variant 1/2.',
            'No whole-module equivalence proof or new throughput measurement in this diagnostic.'])
    destination=ROOT/'results/followup-evaluation-20261016/input-audit.json'
    if destination.exists():
        raise RuntimeError('Keep earlier audits; choose a new output path for a revised audit')
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
