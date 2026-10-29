"""Freeze a targeted follow-up, then produce unreviewed disassembly packets."""
import csv
import hashlib
import json
import random
from prepare_case_reviews import ROOT, packet
from analyze_corpus import acquired_rows
from analyze_malware_sensitivity import COUNTER_SEED


def main():
    path=ROOT/'results/sensitivity/wasmmal-module-audit.csv'
    rows=list(csv.DictReader(path.open(encoding='utf-8',newline='')))
    candidates=[r for r in rows if r['analysis_status']=='ok' and r['counter_reference_body_present']=='True']
    by_label={label:sorted((r for r in candidates if r['author_label']==label and r['sha256']!=COUNTER_SEED),
                          key=lambda r:r['sha256']) for label in ('malware','benign')}
    selected=[];seed=20261008
    for label,pool in by_label.items():
        chosen=pool if label=='benign' else random.Random(seed).sample(pool,min(1,len(pool)))
        for row in chosen:
            selected.append({'sha256':row['sha256'],'stratum':'counter_body_match_'+label,
                             'frame_size':len(pool),'selected_in_stratum':len(chosen),
                             'matched_function_indices':json.loads(row['counter_reference_function_indices_json'])})
    plan_path=ROOT/'experiments/review-selection-stage3.json'
    plan={'seed':seed,'frame':'WasmMal exact matches to increment-bearing reference bodies; previously reviewed seed excluded',
          'selection':'All positive author-benign cases, plus one fixed-random positive author-malware case.',
          'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'selected':selected,
          'scope_limit':'Targeted mechanism follow-up, not a random sample of the full corpus.'}
    if plan_path.exists():
        if json.loads(plan_path.read_text(encoding='utf-8'))!=plan:raise ValueError('selection changed')
    else:plan_path.write_text(json.dumps(plan,indent=2),encoding='utf-8')
    memberships=acquired_rows()
    for row in selected:
        packet(row)
        folder=ROOT/'results/cases'/row['sha256']
        (folder/'memberships.json').write_text(json.dumps([r for r in memberships if r['sha256']==row['sha256']],indent=2),encoding='utf-8')
    print(json.dumps(plan),flush=True)


if __name__=='__main__':main()
