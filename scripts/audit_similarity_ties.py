"""Reweight saved WasmMal measurements under explicit best-reference tie rules.

These are modeling choices, not family labels, population estimates or CIs.
No binaries are executed, and no additional similarity search is performed.
"""
import argparse
import collections
import csv
import datetime
import hashlib
import json
import random
from analyze_malware_sensitivity import ROOT, OUT, MARKERS, THRESHOLDS


def read_records(path):
    rows=[]
    with path.open(encoding='utf-8',newline='') as src:
        for row in csv.DictReader(src):
            if row['author_label']!='malware' or row['analysis_status']!='ok':continue
            for marker in MARKERS:
                value=row[marker]
                if value not in ('True','False',''):raise ValueError((marker,value))
                row[marker]={'True':True,'False':False,'':None}[value]
            row['exact_reference_member']=row['exact_reference_member']=='True'
            row['score']=float(row['best_weighted_body_jaccard'])
            row['ties']=json.loads(row['best_reference_ties_json'])
            if len(row['ties'])!=int(row['best_reference_tie_count']):raise ValueError('tie count mismatch')
            if row['exact_reference_member'] and (row['sha256'] not in row['ties'] or row['score']!=1):
                raise ValueError('anchor must match itself')
            rows.append(row)
    rows.sort(key=lambda r:r['sha256'])
    if len({r['sha256'] for r in rows})!=len(rows):raise ValueError('duplicate SHA')
    return rows


def choose_reference(row,rule,rng=None):
    if row['exact_reference_member']:return row['sha256']
    ties=row['ties']
    if not ties:return None
    if rule=='lex_first':return ties[0]
    if rule=='lex_last':return ties[-1]
    if rule=='ambiguous_singleton':return ties[0] if len(ties)==1 else None
    if rule=='random':return rng.choice(ties)
    raise ValueError(rule)


def summarize(rows,assignments,threshold):
    groups=collections.defaultdict(list)
    for row,reference in zip(rows,assignments,strict=True):
        assigned=reference and threshold is not None and row['score']>=threshold
        key='reference/'+reference if assigned else 'singleton/'+row['sha256']
        groups[key].append(row)
    result={'successful_malware_sha256':len(rows),'groups':len(groups),
            'reference_groups':sum(k.startswith('reference/') for k in groups),
            'reference_assigned_members':sum(len(g) for k,g in groups.items() if k.startswith('reference/')),
            'max_group_members':max(map(len,groups.values()))}
    for marker in MARKERS:
        values=[[r[marker] for r in group if r[marker] is not None] for group in groups.values()]
        nonempty=[v for v in values if v]
        result[marker+'_groups_with_data']=len(nonempty)
        result[marker+'_modules_with_data']=sum(map(len,nonempty))
        result[marker+'_equal_group_mean']=sum(sum(v)/len(v) for v in nonempty)/len(nonempty) if nonempty else None
    return result


def main():
    path=OUT/'wasmmal-module-audit.csv'
    rows=read_records(path)
    outputs=[{'tie_rule':'sha256_only','random_seed':None,'threshold':None,
              **summarize(rows,[None]*len(rows),None)}]
    choices=[('lex_first',None),('lex_last',None),('ambiguous_singleton',None)]+[('random',seed) for seed in range(20)]
    for rule,seed in choices:
        rng=random.Random(seed) if seed is not None else None
        assignments=[choose_reference(row,rule,rng) for row in rows]
        for threshold in THRESHOLDS:
            outputs.append({'tie_rule':rule,'random_seed':seed,'threshold':threshold,
                            **summarize(rows,assignments,threshold)})
    # Independently reproduce the previous lexicographic baseline before
    # accepting results under the new tie rules.
    previous=list(csv.DictReader((OUT/'reference-group-sensitivity.csv').open(encoding='utf-8',newline='')))
    for current,old in zip(outputs[:6],previous,strict=True):
        for key in ('groups','reference_groups','reference_assigned_members','max_group_members'):
            if current[key]!=int(old[key]):raise ValueError(('baseline mismatch',key,current,old))
        for marker in MARKERS:
            key=marker+'_equal_group_mean'
            if abs(current[key]-float(old[key]))>1e-12:raise ValueError(('baseline mismatch',key))
    with (OUT/'tie-sensitivity.csv').open('w',encoding='utf-8',newline='') as dst:
        writer=csv.DictWriter(dst,fieldnames=list(outputs[0]));writer.writeheader();writer.writerows(outputs)
    eligible=[]
    for threshold in THRESHOLDS:
        candidates=[r for r in rows if r['score']>=threshold]
        tied=[r for r in candidates if len(r['ties'])>1 and not r['exact_reference_member']]
        eligible.append({'threshold':threshold,'eligible_members_including_anchors':len(candidates),
                         'ambiguous_nonanchor_members':len(tied),
                         'most_common_tie_sets':[{'references':list(refs),'members':n} for refs,n in
                             collections.Counter(tuple(r['ties']) for r in tied).most_common(5)]})
    summary={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'input':path.relative_to(ROOT).as_posix(),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'successful_malware_sha256':len(rows),'random_seeds':list(range(20)),
             'assignment_rules':{'lex_first':'Smallest best-score reference SHA.',
                                 'lex_last':'Largest best-score reference SHA.',
                                 'ambiguous_singleton':'Nonanchors with multiple best scores remain singleton groups.',
                                 'random':'Uniform draw from each best-score tie set; anchors retain own identity.'},
             'anchor_rule':'Exact reference seeds retain their own identity under every rule.',
             'random_order':'Python random.Random(seed), rows in ascending SHA order; same choices at every threshold.',
             'eligible':eligible,'baseline_reproduction':'all six previous baseline rows reproduced within 1e-12',
             'interpretation':'Sensitivity of descriptive equal-group means to arbitrary tie resolution; random ranges are neither confidence intervals nor worst-case bounds.'}
    (OUT/'tie-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({'rows':len(outputs),'eligible':[{k:v for k,v in r.items() if k!='most_common_tie_sets'} for r in eligible]}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--include-minesweeper',action='store_true')
    args=parser.parse_args()
    if args.include_minesweeper:
        OUT=ROOT/'results/sensitivity-minesweeper'
    main()
