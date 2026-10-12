"""Freeze additional mechanism-validation samples before inspecting outcomes."""
import argparse
import collections
import csv
import hashlib
import json
import random
from analyze_corpus import ROOT, CACHE, acquired_rows
from prepare_case_reviews import packet

PLAN = ROOT / 'experiments/rq-validation-selection.json'
SEED = 20261009


def select():
    if PLAN.exists():
        raise SystemExit('Selection already frozen; use packets, do not resample.')
    rows = acquired_rows()
    prior = set(r['sha256'] for r in csv.DictReader(
        (ROOT/'results/cases/review-index.csv').open(encoding='utf-8')))
    bysha = collections.defaultdict(list)
    for r in rows:
        bysha[r['sha256']].append(r)
    rng = random.Random(SEED)
    selected, frames = [], {}

    def add(r, group, unit):
        assert r['sha256'] not in prior
        selected.append(dict(sha256=r['sha256'], stratum=group,
                             program_unit=unit, selected_path=r['path'],
                             memberships=bysha[r['sha256']]))

    def pick(group, pool, n):
        frames[group] = sorted(pool)
        return rng.sample(sorted(pool), min(n, len(pool)))

    basic = {r['path'].split('/')[-1] for r in rows if r['dataset']=='wasmixer'
             and r['path'].startswith('benchmark/basic-algorithms/origin/')
             and r['path'].split('/')[-1][0].isalpha()}
    for name in pick('wasmixer_basic', basic-{'dekhash.wasm','vowels.wasm'}, 3):
        for transform in ('origin','nameOB','memoryOB'):
            path=f'benchmark/basic-algorithms/{transform}/{name}'
            add(next(r for r in rows if r['dataset']=='wasmixer' and r['path']==path),
                'wasmixer_basic/'+transform,name)
    # The only remaining realworld program; census of that eligible stratum.
    for name in pick('wasmixer_realworld', ['base64-cli.wasm'],1):
        for transform in ('origin','flatten','callindirect'):
            path=f'benchmark/realworld_program/{transform}/{name}'
            add(next(r for r in rows if r['dataset']=='wasmixer' and r['path']==path),
                'wasmixer_realworld/'+transform,name)
    # Utilities avoid treating CryptoNight parameter variants as independent programs.
    for name in pick('cryptic_utilities', ['lcs','needleman_wunsch','seqtk','smith_waterman','tree','wgsim'],2):
        for transform in ('unobfuscated','tigress/flatten'):
            path=f'binaries/{name}/{transform}/{name}.wasm'
            add(next(r for r in rows if r['dataset']=='wasm-obf' and r['path']==path),
                'cryptic_utilities/'+transform,name)
    seismic_pairs={
        'A-Star':('A-Star/wasm_astar.wasm','A-Star/wasm_astar_base_profiled.wasm'),
        'Animation':('Animation/naive.wasm','Animation/naive_profiled.wasm'),
        'Basic4GL':('Basic4GL/basic4gl.wasm','Basic4GL/basic4gl.base_profiled.wasm'),
        'CreaturePack':('CreaturePack/creaturepack-wasm.wasm','CreaturePack/creaturepack.base_profiled.wasm')}
    for name in pick('seismic_nonmining',seismic_pairs,2):
        for role,path in zip(('original','profiled'),seismic_pairs[name]):
            add(next(r for r in rows if r['dataset']=='seismic' and r['path']==path),
                'seismic_nonmining/'+role,name)
    # Cross-corpus samples are exploratory: unknown program ancestry cannot be
    # certified disjoint by SHA alone. Do not pool with program-held-out controls.
    for ds, prefix in [('swamped','experimental_data/'),('wasmmal','malware/')]:
        pool=sorted({r['sha256'] for r in rows if r['dataset']==ds and r['path'].startswith(prefix)}-prior)
        strata={'loop':[], 'no_loop':[]}
        for sha in pool:
            f=CACHE/(sha+'.json')
            if not f.exists(): continue
            d=json.loads(f.read_text(encoding='utf-8'))
            if d['status']!='ok': continue
            strata['loop' if d.get('br_table_in_loop_count',0) else 'no_loop'].append(sha)
        for kind,pool in strata.items():
            for sha in pick(ds+'/'+kind,pool,2):
                add(next(r for r in bysha[sha] if r['dataset']==ds),ds+'/'+kind,'unknown_ancestry')
    protocol={
        'seed':SEED, 'prior_review_sha256':sorted(prior),
        'evaluation_unit':'specified function/transformation site; no whole-module absence verdict',
        'split':'new named control programs; exploratory unknown-parent corpus samples separately',
        'baseline':'presence of br_table / call_indirect / nop / XOR is candidate only',
        'criteria':{
            'flattening':'trace selector definition, state writes, return to dispatcher, and correspondence to original; state machine alone insufficient',
            'instrumentation':'increment target, read/reset interface, paired original and public implementation correspondence',
            'call_indirection':'match original direct target to transformed constant/table entry; ordinary function pointers are alternative',
            'renaming':'changed names with decoded bodies and operands compared, separating LEB reencoding',
            'memory':'trace replacement helpers and effective key values, do not equate XOR with encryption',
            'redundancy':'local operand semantics; no inference of author intent or global equivalence'},
        'outcomes':['confirmed_mechanism','ordinary_processing','instrumentation','unresolved','analysis_failed'],
        'validation':'mechanical checks on known pilot pairs first; independent human review remains pending',
        'limits':'no population prevalence or classifier accuracy without independent reference labels',
        'frames':frames, 'selected':selected}
    PLAN.write_text(json.dumps(protocol,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'selected':len(selected),'unique':len({r['sha256'] for r in selected}),
                      'programs':sorted({r['program_unit'] for r in selected})}))


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['select','packets']); a=ap.parse_args()
    if a.action=='select': select()
    else:
        for row in json.loads(PLAN.read_text(encoding='utf-8'))['selected']:
            packet(row)
