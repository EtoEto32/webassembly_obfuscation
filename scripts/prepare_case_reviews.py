"""Freeze a reproducible first-stage sample and prepare unreviewed evidence.

Sampling is within the listed acquired corpora, not the Web or final cross-
corpus population. Packets are navigation aids, never automatic verdicts.
"""
import argparse
import collections
import datetime
import hashlib
import json
import random
import re
import subprocess
from analyze_corpus import ROOT, CACHE, WABT, acquired_rows, sections

SEED=20261006
PLAN=ROOT/'experiments/review-selection-stage1.json'


def select():
    rows=acquired_rows()
    by_sha=collections.defaultdict(list)
    for r in rows: by_sha[r['sha256']].append(r)
    sw={s for s,rs in by_sha.items() if any(r['dataset']=='swamped' and r['path'].startswith('experimental_data/') for r in rs)}
    wm={s for s,rs in by_sha.items() if any(r['dataset']=='wasmmal' and r['path'].startswith('malware/') for r in rs)}
    benign={s for s,rs in by_sha.items() if any(r['dataset']=='wasmmal' and r['path'].startswith('benign/') for r in rs)}
    reference=sw|{s for s,rs in by_sha.items() if any(r['dataset']=='wasmbench' for r in rs)}
    candidates={'swamped_loop':[],'swamped_no_loop':[],'wasmmal_nonreference_high_entropy':[],
                'wasmmal_nonreference_low_entropy':[],'wasmmal_benign_high_entropy':[],
                'wasmmal_benign_low_entropy':[],'wasmmal_reference_outside_swamped':[],
                'wasmmal_nonreference_no_data':[],'wasmmal_benign_no_data':[]}
    exclusions=[]; population=[]
    for sha in sorted(sw|wm|benign):
        path=CACHE/(sha+'.json')
        if not path.exists():
            exclusions.append({'sha256':sha,'reason':'analysis_pending'}); continue
        data=json.loads(path.read_text())
        if data['status']!='ok':
            exclusions.append({'sha256':sha,'reason':data['status']}); continue
        ent=data.get('data_section_entropy')
        entropy_group='no_data' if ent is None else 'high_entropy' if ent>=7 else 'low_entropy'
        if sha in sw:
            stratum='swamped_loop' if data.get('br_table_in_loop_count',0) else 'swamped_no_loop'
        elif sha in wm:
            stratum='wasmmal_reference_outside_swamped' if sha in reference else 'wasmmal_nonreference_'+entropy_group
        else:
            stratum='wasmmal_benign_'+entropy_group
        candidates[stratum].append(sha)
        population.append({'sha256':sha,'stratum':stratum,'data_section_entropy':ent,
                           'br_table_in_loop_count':data.get('br_table_in_loop_count',0)})
    quotas={'swamped_loop':4,'swamped_no_loop':4,'wasmmal_nonreference_high_entropy':3,
            'wasmmal_nonreference_low_entropy':3,'wasmmal_benign_high_entropy':2,
            'wasmmal_benign_low_entropy':2,'wasmmal_reference_outside_swamped':2,
            'wasmmal_nonreference_no_data':1,'wasmmal_benign_no_data':1}
    rng=random.Random(SEED); selected=[]
    for stratum,pool in candidates.items():
        for sha in rng.sample(sorted(pool),min(quotas[stratum],len(pool))):
            selected.append({'sha256':sha,'stratum':stratum,'frame_size':len(pool),
                             'selected_in_stratum':min(quotas[stratum],len(pool)),
                             'memberships':by_sha[sha]})
    pop=json.dumps(population,sort_keys=True).encode()
    plan={'version':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'seed':SEED,'frame':'acquired SWAMPED experimental seeds and WasmMal root labels with successful static analysis',
          'scope_limit':'first-stage acquired-corpus sample; excludes failed analysis and does not estimate Internet prevalence',
          'entropy_threshold':7,'population_sha256':hashlib.sha256(pop).hexdigest(),
          'quotas':quotas,'frame_counts':{k:len(v) for k,v in candidates.items()},
          'excluded':exclusions,'selected':selected}
    PLAN.write_text(json.dumps(plan,indent=2),encoding='utf-8')
    (PLAN.parent/'review-frame-stage1.json').write_bytes(pop)
    print('selected',len(selected),'excluded',len(exclusions),plan['frame_counts'],flush=True)


def packet(row):
    sha=row['sha256']; data=json.loads((CACHE/(sha+'.json')).read_text())
    folder=ROOT/'results/cases'/sha; folder.mkdir(parents=True,exist_ok=True)
    obj=ROOT/data['object']
    if data.get('disassembly_input','original')!='original':
        raw=obj.read_bytes()
        core=raw[:8]+b''.join(s['raw'] for s in sections(raw) if s['id']!=0)
        obj=folder/'review-core.wasm'
        obj.write_bytes(core)
    dest=folder/'disassembly.txt'
    if not dest.exists():
        with dest.open('wb') as out:
            subprocess.run([str(WABT/'wasm-objdump.exe'),'-d',str(obj)],stdout=out,check=True,timeout=120)
    lines=dest.read_text().splitlines()
    funcs=[]; current=None
    for i,line in enumerate(lines):
        match=re.search(r'func\[(\d+)\]',line)
        if match:
            if current: current['end']=i
            current={'index':int(match[1]),'start':i}; funcs.append(current)
    if current: current['end']=len(lines)
    fmap={f['index']:f for f in funcs}
    # All branch-table sites are indexed; excerpts prioritize large tables.
    sites=[{'line':i+1,'text':line} for i,line in enumerate(lines) if '| br_table' in line or re.search(r'\|\s+br_table\b',line)]
    (folder/'branch-table-sites.json').write_text(json.dumps(sites,indent=2),encoding='utf-8')
    stats=sorted(data['functions'],key=lambda f:(f['max_br_table_targets'],f['br_table_in_loop'],f['instruction_count']),reverse=True)
    chosen=stats[:2]
    excerpts=[]
    for f in chosen:
        bounds=fmap.get(f['function_index'])
        if not bounds: continue
        start,end=bounds['start'],bounds['end']
        excerpts.append('\nFUNCTION '+json.dumps(f)+'\n')
        if end-start<=220:
            ranges=[(start,end)]
        else:
            hits=[i for i in range(start,end) if re.search(r'\|\s+br_table\b',lines[i])][:3]
            ranges=[(start,min(start+35,end))]+[(max(start,i-45),min(end,i+55)) for i in hits]
        emitted=set()
        for a,b in ranges:
            for i in range(a,b):
                if i not in emitted: excerpts.append(f'{i+1}: {lines[i]}'); emitted.add(i)
    (folder/'excerpts.txt').write_text('\n'.join(excerpts),encoding='utf-8')
    meta={k:data.get(k) for k in ['sha256','analyzer_version','status','bytes','defined_functions','instruction_count','name_section','data_section_entropy','code_section_entropy','br_table_in_loop_count','max_br_table_targets','data_ascii_strings_preview','imports','exports']}
    meta.update(selection=row,packet_status='unreviewed_navigation_aid',indexed_br_table_sites=len(sites),selected_function_indices=[f['function_index'] for f in chosen])
    meta['disassembly_input']=data.get('disassembly_input','original')
    meta['offset_scope']='original binary' if meta['disassembly_input']=='original' else 'custom sections stripped; offsets do not refer to original binary'
    (folder/'packet.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(sha,row['stratum'],'packet_ready',len(sites),'br_table sites',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['select','packets']); args=ap.parse_args()
    if args.action=='select':
        if PLAN.exists(): raise SystemExit('Selection exists; do not silently resample')
        select()
    else:
        for row in json.loads(PLAN.read_text())['selected']: packet(row)
