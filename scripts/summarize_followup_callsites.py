"""Join audited dynamic counters with saved lexical call-site contexts."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/followup-evaluation-20261016'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run',type=Path);args=parser.parse_args()
    run=args.run.resolve();plan_path=run/'inputs/plan.json';plan=json.loads(plan_path.read_text(encoding='utf-8'))
    audit_path=run/'paths-audit.json';audit=json.loads(audit_path.read_text(encoding='utf-8'));assert audit['status']=='passed'
    raw_path=run/'outputs/paths.json';raw=json.loads(raw_path.read_text(encoding='utf-8'));assert audit['measurement_sha256']==sha(raw_path)
    review_path=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/xmr-helper-path-review.json'
    review=json.loads(review_path.read_text(encoding='utf-8'))
    records=[]
    for inventory in plan['path_diagnostic']['callsite_inventory']:
        assert sha(ROOT/inventory['source_path'].replace('\\','/'))==inventory['source_sha256']
        for row in raw['counts']:
            if row['id']!=inventory['id']:continue
            sites=[dict(site,hash_calls=int(row['hash_deltas'][site['counter']])) for site in inventory['sites']]
            total=sum(site['hash_calls'] for site in sites);entry=int(row['hash_deltas']['f118'])
            assert total==entry,'Unexplained indirect or missing call-site coverage'
            result=dict(id=row['id'],vector_id=row['vector_id'],helper_entry_calls=entry,
                direct_callsite_total=total,unexplained_calls=entry-total,sites=sites)
            if row['id']=='original':
                expected_scopes=[[c['construct'] for c in site['enclosing_constructs']]
                    for site in review['reference_call_contexts'] if site['callee']=='$f118']
                assert [site['enclosing_constructs'] for site in sites]==expected_scopes
                main=[site for site in sites if 'loop $L17' in site['enclosing_constructs']]
                direct=[site for site in main if site['enclosing_constructs']==['block $B16','loop $L17']]
                assert len(direct)==2
                result['reviewed_original_loop_L17_calls']=sum(site['hash_calls'] for site in main)
                result['reviewed_original_direct_L17_calls']=sum(site['hash_calls'] for site in direct)
                result['nested_L17_calls']=result['reviewed_original_loop_L17_calls']-result['reviewed_original_direct_L17_calls']
                result['L17_lexical_sites']=len(main)
                result['L17_executed_sites']=sum(site['hash_calls']>0 for site in main)
                result['other_direct_calls']=entry-result['reviewed_original_loop_L17_calls']
            records.append(result)
    result=dict(status='audited-site-sums-match-helper-entry-counts',records=records,
        plan_sha256=sha(plan_path),measurement_sha256=sha(raw_path),audit_sha256=sha(audit_path),
        main_loop_interpretation='Original L17 has four lexical f118 sites, including two within an additional block; distinguish the two direct sites from all sites enclosed by L17. Scopes are checked against the preserved review. Other variants retain raw lexical scopes without assuming identical label meaning.',
        existing_review_path='results/runtime-mining/cross-dataset/proof-of-theft/xmr-helper-path-review.json',
        existing_review_sha256=sha(ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/xmr-helper-path-review.json'),
        limitations=['Counts do not measure time shares or native instruction counts.',
            'Finite cn/0 inputs; no all-variant or all-path coverage claim.'],script_sha256=sha(Path(__file__)))
    destination=OUT/'callsite-summary.json';assert not destination.exists()
    destination.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([dict(id=r['id'],vector_id=r['vector_id'],total=r['helper_entry_calls'],
        reviewed_original_loop=r.get('reviewed_original_loop_L17_calls')) for r in records],indent=2))


if __name__=='__main__':main()
