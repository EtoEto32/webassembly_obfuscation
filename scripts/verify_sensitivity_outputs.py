"""Check completed result scope, input identities, and cross-file consistency."""
import collections
import csv
import datetime
import hashlib
import json
from analyze_corpus import ROOT
from analyze_malware_sensitivity import OUT


def read_csv(name):
    return list(csv.DictReader((OUT/name).open(encoding='utf-8',newline='')))


def main():
    modules=read_csv('wasmmal-module-audit.csv')
    hashes={r['sha256'] for r in modules}
    assert len(hashes)==len(modules)==15024
    labels=collections.Counter(r['author_label'] for r in modules)
    assert labels=={'malware':7512,'benign':7512}
    assert collections.Counter(r['analysis_status'] for r in modules)=={'ok':15020,'read_failed':2,'validation_failed':2}
    input_sha=hashlib.sha256((OUT/'wasmmal-module-audit.csv').read_bytes()).hexdigest()
    for name in ('tie-summary.json','counter-cohort-summary.json'):
        assert json.loads((OUT/name).read_text())['input_sha256']==input_sha
    selected={r['sha256'] for r in modules if r['counter_reference_body_present']=='True'}
    counters=read_csv('counter-cohort-direct.csv')
    assert len(counters)==len(selected)==124
    assert {r['sha256'] for r in counters}==selected
    receipts={r['sha256']:r for r in map(json.loads,(OUT/'analysis-inputs.jsonl').read_text().splitlines())}
    for row in counters:
        assert row['status']=='ok'
        assert row['cache_sha256']==receipts[row['sha256']]['cache_sha256']
        assert int(row['direct_motif_sequences'])>=int(row['exact_body_sequences'])
        assert int(row['direct_motif_instructions'])==4*int(row['direct_motif_sequences'])
        assert int(row['direct_motif_instructions'])<=int(row['instruction_count'])
        checks=json.loads(row['counter_support_checks_json'])
        exceptions=json.loads(row['counter_support_exceptions_json'])
        assert set(exceptions)=={k for k,v in checks.items() if not v}
    ties=read_csv('tie-sensitivity.csv')
    assert len(ties)==116
    assert all(int(r['successful_malware_sha256'])==7510 for r in ties)
    for row in ties:
        if row['tie_rule']=='sha256_only':continue
        assert int(row['reference_groups'])==56
        assert 56<=int(row['reference_assigned_members'])<=7510
    generation=json.loads((OUT/'figures/generation.json').read_text())
    for item in generation['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
    review=json.loads((ROOT/'results/cases/review-status.json').read_text())
    stage=next(r for r in review['stages'] if r['stage']=='stage3')
    assert stage['reviewed']==stage['selected']==4 and stage['pending']==0
    script_names=['analyze_malware_sensitivity.py','audit_similarity_ties.py','audit_counter_cohort.py',
                  'prepare_counter_reviews.py','plot_malware_sensitivity.py','verify_sensitivity_outputs.py']
    result={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'wasmmal_unique':15024,'analysis_successes':15020,'analysis_failures':4,
            'counter_positive_direct_audits':124,'tie_summary_rows':116,'formal_stage3_reviews':4,
            'status':'scope_and_consistency_checks_passed',
            'limits':'Consistency verification is not independent scientific review, full-corpus completion, or obfuscation ground truth.',
            'script_sha256':{name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in script_names}}
    (OUT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
