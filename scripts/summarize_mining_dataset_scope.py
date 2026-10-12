"""Separate source declarations, directory contents, and confirmed mechanisms."""
import collections
import csv
import hashlib
import json
from pathlib import Path
from analyze_corpus import acquired_rows

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/mining-methods'


def save_csv(name, rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        w.writeheader();w.writerows(rows)


def main():
    cohorts=list(csv.DictReader((ROOT/'results/corpus/cohort-summary.csv').open(encoding='utf-8')))
    selected={
        'minesweeper/miner_samples':'collected miner samples',
        'minesweeper/crawled_sites':'historical crawl distribution; original validation failed',
        'swamped/Cryptojackers_43':'author-labeled cryptojacker seeds',
        'swamped/Malware_31':'other malware; contextual reference, not all miners',
        'swamped/tool_examples':'tool examples; not the generated evaluation corpus',
        'proof-of-theft/obfuscated_miners':'directory contents including originals, instrumented versions and intermediate objects; NOT verified transformed-miner count',
        'proof-of-theft/other_mining_artifacts':'other mining distribution contents',
        'wasmmal/malware':'author-labeled malware; mining function not independently confirmed for every file',
        'wasmmal/benign':'non-mining-specific contextual control',
        'wasmbench/filtered_release':'general-purpose contextual control',
    }
    present={r['cohort'] for r in cohorts}
    # Fail instead of silently losing a requested source due to label drift.
    missing=set(selected)-present
    if missing:
        print('Available matching labels:',[r['cohort'] for r in cohorts if r['cohort'].startswith(('swamped/','wasmbench/'))])
        raise ValueError(missing)
    rows=[]
    for r in cohorts:
        if r['cohort'] not in selected:continue
        x=dict(r,interpretation=selected[r['cohort']],mechanism_prevalence='not estimated')
        n=int(r['analyzed_ok'])
        for key in ('br_table_in_loop_count_present','call_indirect_count_present','nop_count_present'):
            x[key+'_percent']=100*int(r[key])/n if n else None
        rows.append(x)
    save_csv('dataset-feature-context.csv',rows)

    proof=[r for r in acquired_rows(['proof-of-theft']) if '___obfuscated_miners/' in r['path']]
    groups=collections.defaultdict(list)
    for r in proof:
        directory=r['path'].split('___obfuscated_miners/')[1].split('/')[0]
        groups[directory].append(r)
    methods={
        'emccobf_substitution':'emcc-obf/substitution',
        'emccobf_flattening':'emcc-obf/flattening',
        'emccobf_boguscf':'emcc-obf/boguscf',
        'emccobf_split':'emcc-obf/split',
        'encodearith':'tigress/encodearith',
        'fsplitflatten':'tigress/split+flatten',
        'fflatten':'tigress/flatten',
        'fsplit':'tigress/split',
        'virtualize':'tigress/virtualize',
    }
    inventory=[]
    for directory,rs in sorted(groups.items()):
        norm=directory.replace('-','_')
        matches=[(suffix,method) for suffix,method in methods.items() if norm.endswith(suffix)]
        assert len(matches)==1,(directory,matches)
        suffix,method=matches[0]
        inventory.append(dict(directory=directory,declared_method=method,
            source_program_label=norm[:-len(suffix)].rstrip('_'),
            acquired_member_occurrences=len(rs),unique_sha256=len({r['sha256'] for r in rs}),
            evidence_level='directory-declared setting; member role not fully resolved',
            verified_transformed_module_count='',
            source='data/catalog/proof-of-theft/artifact-description.txt'))
    save_csv('proof-of-theft-setting-inventory.csv',inventory)
    save_csv('proof-of-theft-member-inventory.csv',proof)
    sums=[]
    for m in sorted({r['declared_method'] for r in inventory}):
        rs=[r for r in inventory if r['declared_method']==m]
        sums.append(dict(declared_method=m,setting_directories=len(rs),
                         program_labels=len({r['source_program_label'] for r in rs}),
                         interpretation='count of directory-declared settings, not confirmed obfuscation prevalence'))
    save_csv('proof-of-theft-declared-settings.csv',sums)
    report=dict(
        source_cohort_table_sha256=hashlib.sha256((ROOT/'results/corpus/cohort-summary.csv').read_bytes()).hexdigest(),
        selected_cohorts=len(rows),proof_setting_directories=len(inventory),
        proof_static_members=len(proof),
        findings=[
          'The 128 unique hashes in the existing obfuscated_miners cohort are directory contents, not 128 verified obfuscated final programs.',
          'Members include .orig.wasm files, out/ variants, and .o intermediate objects. Setting-directory counts must not be interpreted as binary prevalence.',
          'SWAMPED downloaded seeds and examples do not equal the transformed evaluation corpus in the paper.',
          'Feature percentages are conditional on successful static analysis; they are not method prevalence.',
          'WasmMal malware labels alone do not establish that every sample is cryptojacking-related.'
        ],
        remaining=['Resolve final program, uninstrumented and instrumented roles in Proof-of-Theft before paired comparisons.',
                   'Representative mechanism findings do not justify per-method prevalence for unreviewed files.'],
        reproduction='python scripts/summarize_mining_dataset_scope.py')
    (OUT/'dataset-scope-log.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
