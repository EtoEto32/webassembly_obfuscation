"""Verify unchanged measurements and compare 56/60-anchor sensitivity models."""
import collections
import csv
import datetime
import hashlib
import json
from analyze_corpus import ROOT


def read_csv(path):
    with path.open(encoding='utf-8',newline='') as src:return list(csv.DictReader(src))


def main():
    old=ROOT/'results/sensitivity';new=ROOT/'results/sensitivity-minesweeper'
    previous={r['sha256']:r for r in read_csv(old/'wasmmal-module-audit.csv')}
    current={r['sha256']:r for r in read_csv(new/'wasmmal-module-audit.csv')}
    if previous.keys()!=current.keys():raise ValueError('Module universe changed')
    changed=collections.Counter()
    allowed={'exact_reference_member','best_reference_sha256','best_weighted_body_jaccard',
             'best_reference_tie_count','best_reference_ties_json'}
    for sha,left in previous.items():
        right=current[sha]
        if left.keys()!=right.keys():raise ValueError('Measurement fields changed')
        for field in left:
            if left[field]!=right[field]:
                changed[field]+=1
                if field not in allowed:raise ValueError('Non-reference measurement changed: '+field)
    old_ties=read_csv(old/'tie-sensitivity.csv');new_ties=read_csv(new/'tie-sensitivity.csv')
    key=lambda r:(r['tie_rule'],r['random_seed'],r['threshold'])
    indexed={key(r):r for r in old_ties};comparisons=[]
    for row in new_ties:
        before=indexed[key(row)]
        if row['tie_rule'] not in ('sha256_only','lex_first','ambiguous_singleton'):continue
        comparisons.append({'tie_rule':row['tie_rule'],'threshold':row['threshold'],
            'old_groups':int(before['groups']),'new_groups':int(row['groups']),
            'old_loop_marker_group_mean':float(before['br_table_in_loop_equal_group_mean']),
            'new_loop_marker_group_mean':float(row['br_table_in_loop_equal_group_mean'])})
    report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'same_module_universe':True,'modules':len(previous),'all_nonreference_measurements_unchanged':True,
            'changed_reference_fields':dict(changed),'loop_marker_comparison':comparisons,
            'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                      for folder in (old,new) for p in (folder/'wasmmal-module-audit.csv',folder/'tie-sensitivity.csv')],
            'interpretation':'This expands the reference set, not the measured malware sample. Groups remain a similarity model, not verified parents/families.'}
    (new/'reference-expansion-comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='inputs'}),flush=True)


if __name__=='__main__':main()
