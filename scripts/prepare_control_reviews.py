"""Fixed-seed paired control review; no prevalence estimator."""
import argparse
import collections
import datetime
import hashlib
import json
import random
from analyze_corpus import ROOT, acquired_rows
from prepare_case_reviews import packet

PLAN=ROOT/'experiments/review-selection-stage2.json'


def select():
    if PLAN.exists(): raise SystemExit('Selection exists; do not silently resample')
    rows=acquired_rows(); rng=random.Random(20261007)
    bysha=collections.defaultdict(list)
    for r in rows: bysha[r['sha256']].append(r)
    frames={
        'wasmixer_basic_named':sorted({r['path'].split('/')[-1] for r in rows if r['dataset']=='wasmixer'
             and r['path'].startswith('benchmark/basic-algorithms/origin/') and r['path'].split('/')[-1][0].isalpha()}),
        'wasmixer_realworld':sorted({r['path'].split('/')[-1] for r in rows if r['dataset']=='wasmixer' and r['path'].startswith('benchmark/realworld_program/origin/')}),
        'cryptic_controls':sorted({r['path'].split('/')[1] for r in rows if r['dataset']=='wasm-obf-controls'})}
    choices={k:rng.sample(v,2 if k=='wasmixer_basic_named' else 1) for k,v in frames.items()}
    selected=[]
    for frame,names in choices.items():
        for name in names:
            transforms=['origin','nameOB','memoryOB'] if frame=='wasmixer_basic_named' else ['origin','flatten','callindirect'] if frame=='wasmixer_realworld' else ['unobfuscated','tigress/flatten']
            for transform in transforms:
                dataset='wasm-obf-controls' if frame=='cryptic_controls' else 'wasmixer'
                p=f'binaries/{name}/{transform}/{name}.wasm' if frame=='cryptic_controls' else f"benchmark/{'basic-algorithms' if frame=='wasmixer_basic_named' else 'realworld_program'}/{transform}/{name}"
                r=next(r for r in rows if r['dataset']==dataset and r['path']==p)
                selected.append({'sha256':r['sha256'],'stratum':frame+'/'+transform,
                                 'frame_size':len(frames[frame]),'selected_in_stratum':len(names),
                                 'paired_program':name,'selected_path':p,'memberships':bysha[r['sha256']]})
    plan={'version':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'seed':20261007,'selection_unit':'program name, followed by paired variants',
          'frame':'named basic algorithms, realworld_program controls, and initial Cryptic Bytes 12-program control subset',
          'scope_limit':'paired control review; not a malware prevalence sample; basic named subset excludes numeric-name synthetic alias benchmarks',
          'frames':frames,'choices':choices,'selected':selected}
    PLAN.write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print(json.dumps({'choices':choices,'selected':len(selected),'unique':len({r['sha256'] for r in selected})}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['select','packets']);args=ap.parse_args()
    if args.action=='select': select()
    else:
        for row in json.loads(PLAN.read_text())['selected']: packet(row)
