"""Export occurrence provenance and aggregate static observations, never labels."""
import collections
import csv
import itertools
import json
import statistics
from pathlib import Path
from analyze_corpus import ROOT, CACHE, OUT, VERSION, acquired_rows


def csv_write(name,rows):
    if not rows: return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def annotate(r,wasmmal_labels,prior,control_pairs=None,release_parents=None,wasmizer_metadata=None):
    d,p=r['dataset'],r['path'].replace('\\','/')
    a={'author_label':'unlabeled','label_basis':'none','provenance':'unknown',
       'platform':'unknown','cohort':d,'transformation':'unknown','parent_id':'',
       'observed_date':'','observed_date_basis':'unavailable'}
    if d=='wasmmal':
        label=wasmmal_labels.get(r['sha256'],'unknown')
        a.update(author_label=label,label_basis='author root directory; paper reports VirusTotal labeling',
                 provenance='source_corpus_or_generated_not_individually_disclosed' if label=='malware' else 'source_corpus_member_per_paper',
                 cohort=d+'/'+('split-'+p.split('/')[1] if p.startswith('Data_NewSplit/') else label))
        if r['sha256'] in prior:
            a['reference_corpus_exact_match']=True
            a['provenance']='exact_match_to_reference_seed_or_source_corpus'
    elif d=='swamped':
        a['platform']='browser'
        if p.startswith('experimental_data/'):
            a.update(author_label='cryptojacker' if 'Cryptojackers_43/' in p else 'malware',
                     label_basis='author experimental_data group; paper section IV',
                     provenance='reference_seed_from_prior_datasets',cohort=d+'/'+p.split('/')[1],transformation='seed_not_proven_unobfuscated')
        else:
            a.update(cohort=d+'/tool_examples',provenance='tool_example_unknown_transform')
    elif d=='wasmbench':
        a.update(provenance='collected_from_mixed_sources',cohort=d+'/filtered_release',
                 label_basis='general-purpose dataset; no benign inference')
    elif d=='wasmixer':
        parts=p.split('/')
        group=parts[1] if len(parts)>1 else 'unknown'
        transform=parts[2] if len(parts)>3 and group in ('basic-algorithms','realworld_program') else 'unknown'
        a.update(cohort=d+'/'+group+'/'+transform,transformation=transform,
                 declared_transformation=transform,
                 provenance='author_transform_directory_not_verified' if transform!='unknown' and transform!='origin' else 'benchmark_or_collected_seed',
                 label_basis='author benchmark path; no independent malware verdict')
        if group=='mining_programs':
            a.update(author_label='cryptomining',provenance='collected_seed_per_paper',platform='browser')
        if transform!='unknown': a['parent_id']=group+'/'+Path(p).name
        pair=(control_pairs or {}).get(p)
        if pair:
            a.update(parent_id=pair['parent_id'],parent_sha256=pair['origin_sha256'],
                     parent_basis=pair['pairing_evidence'],control_label_validation=pair['control_label_validation'])
            if pair['exact_bytes_equal']:
                a.update(transformation='identical_bytes_to_origin',provenance='duplicate_of_author_origin')
    elif d=='wasm-obf-controls':
        transform='flatten' if '/flatten/' in p else 'original'
        a.update(cohort=d+'/'+transform,provenance='controlled_compilation',author_label='non_mining_program',
                 transformation=transform,label_basis='selected game/utility build paths',platform='browser')
    elif d=='wasm-obf':
        parent=(release_parents or {}).get(p)
        if parent:
            a.update(cohort=d+'/'+parent['release_variant']+'/'+parent['declared_transformation'].split('/')[0],
                     provenance='author_generated_control',platform='browser',
                     author_label='cryptomining' if parent['program_category']=='miners' else 'non_mining_program',
                     label_basis='pinned author dataset source directory; not a malicious-deployment verdict',
                     declared_transformation=parent['declared_transformation'],
                     transformation=parent['observed_transformation'],
                     parent_id=parent['parent_id'],parent_sha256=parent['parent_sha256'],
                     parent_basis=parent['parent_basis'],
                     comparison_baseline_sha256=parent['comparison_baseline_sha256'],
                     program_category=parent['program_category'])
        else:
            a.update(cohort=d+'/repository_examples',provenance='repository_example_not_release_lineage_verified')
    elif d=='minerray':
        a.update(cohort=d+'/'+p.rsplit('/',1)[0],provenance='collected_per_repository',platform='browser')
    elif d=='diversification2022':
        a.update(cohort=d+'/'+r.get('artifact','repository_examples'),provenance='research_artifact_provenance_pending')
    elif d=='industry2025':
        a.update(cohort=d+'/validwasm',provenance='deployed_web_collection_per_paper',
                 platform='browser_collection_context',label_basis='no per-binary malware labels in downloaded archive')
    elif d=='wobfuscator':
        embedded=bool(r.get('source_js_path'))
        dependency=bool(r.get('dependency_path')) or '/node_modules/' in p
        a.update(cohort=d+('/js_literals' if embedded else '/standalone')+('/dependencies' if dependency else '/project'),
                 provenance='packaged_dependency' if dependency else 'author_translation_project',
                 label_basis='six published library projects; not the full malicious evaluation set',
                 embedded_wasm=embedded,observed_js_encoding=r.get('js_encoding',''),
                 source_project_id=r.get('artifact','').removesuffix('-js'),
                 provenance_note='literal presence does not establish runtime use or JS-to-Wasm transformation of each module')
    elif d=='androwasm':
        poc='/case_studies/' in p
        subtype='ransomware' if 'ransom' in p else 'spyware' if 'spyware' in p else 'execution_example'
        a.update(cohort=d+'/'+subtype,platform='Android',
                 provenance='author_generated_poc' if poc else 'author_execution_example',
                 author_label=subtype+'_poc' if poc else 'example',
                 label_basis='author case-study path; not a collected field-malware verdict',
                 source_project_id='androwasm/'+subtype,
                 provenance_note='APK-level obfuscation names do not establish changes to embedded Wasm')
    elif d=='seismic':
        a.update(cohort=d+'/'+('profiled_name' if 'profiled' in p.lower() or 'inlined' in p.lower() else 'other'),
                 provenance='research_collection_and_instrumentation_mixed',platform='browser_collection_context',
                 label_basis='profiling artifacts and collected programs require separate verification')
    elif d=='proof-of-theft':
        group='nonminers' if 'nonminers/' in p or '___nonminers/' in p else 'obfuscated_miners' if 'miner-obfuscated/' in p or '___obfuscated_miners/' in p else 'other_mining_artifacts'
        a.update(cohort=d+'/'+group,provenance='research_artifact_with_originals_and_instrumented_copies',
                 platform='browser_research_context',
                 author_label='non_mining_program' if group=='nonminers' else 'cryptomining',
                 label_basis='author artifact directory; mining is not a malicious-deployment verdict',
                 declared_transformation='obfuscation_directory' if group=='obfuscated_miners' else 'unknown')
    elif d=='wbd':
        a.update(cohort=d+'/'+r.get('artifact','unknown'),provenance='benchmark_and_vulnerability_test_collection',
                 platform='WASI_benchmark_context',label_basis='anomaly/vulnerability labels are not malware labels')
    elif d=='wasim':
        a.update(cohort=d+'/packaged_examples',provenance='tool_repository_examples',
                 label_basis='packaged Wasm API examples; not full paper evaluation corpus')
    elif d=='deepminer':
        a.update(cohort=d+'/mining_implementation',provenance='published_mining_software',
                 author_label='cryptomining',label_basis='mining software; no malicious-deployment verdict')
    elif d=='minesweeper':
        if r.get('artifact')=='minesweeper-crawled':
            a.update(cohort=d+'/crawled_sites',provenance='author_crawled_website_archive',
                     platform='browser_collection_context',
                     label_basis='README describes drive-by-mining websites; no independent per-binary verdict')
        else:
            group='benign_samples' if '/benign_samples/' in p else 'miner_samples' if '/miner_samples/' in p else 'other'
            a.update(cohort=d+'/'+group,provenance='author_repository_reference_sample',
                     author_label='benign' if group=='benign_samples' else 'cryptomining' if group=='miner_samples' else 'unlabeled',
                     platform='browser_collection_context',
                     label_basis='author wasm_samples directory; mining label alone is not malicious deployment')
    elif d=='wasm-r3':
        a.update(cohort=d+'/OOPSLA2024_benchmarks',provenance='author_generated_record_replay_benchmark',
                 platform='standalone_replay_of_browser_program',
                 transformation='record_reduce_replay_per_author',
                 label_basis='27 author benchmarks; generated replay artifacts are not unmodified field binaries',
                 source_project_id='wasm-r3/'+Path(p).stem)
    elif d=='wasmizer':
        a.update(cohort=d+'/MSR2023_snapshot',provenance='repository_collection_and_author_compilation_mixed',
                 label_basis='general-purpose corpus; publication does not imply benignness',
                 observed_date_basis='December 2022 collection interval per artifact README; not per-binary first-seen date')
        metadata=(wasmizer_metadata or {}).get(r.get('sha256'))
        if metadata:
            a.update(source_paths_json=json.dumps(metadata.get('source_paths',[])),
                     source_project_folders_json=json.dumps(metadata.get('source_project_folders',[])),
                     source_test_path_evidence=metadata.get('test_path_evidence'),
                     source_dependency_path_evidence=metadata.get('dependency_path_evidence'),
                     source_wat_path_evidence=metadata.get('wat_source_path_evidence'),
                     source_metadata_status=metadata['metadata_status'])
    if r['sha256']=='aafff58765c917b0900726ecca11c715c38c3c25b1be9e0af130e0f5b170c14e':
        a.update(observed_instrumentation='confirmed_instruction_counters',
                 observed_instrumentation_evidence='results/cases/aafff58765c917b0900726ecca11c715c38c3c25b1be9e0af130e0f5b170c14e/review-stage1.md',
                 provenance_note='same binary in SEISMIC CoinHive/64-bit; counter implementation agrees with pinned inline_counter64.py; not an unmodified field specimen')
    return {**r,**a}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=acquired_rows(include_unhashed=True)
    # Historical hand-picked controls were re-extracted from the same releases.
    # Their local copies are not another dataset or another upstream occurrence.
    excluded_controls=0
    if any(r.get('artifact')=='wasm-obf-release-binaries' for r in rows):
        excluded_controls=sum(r['dataset']=='wasm-obf-controls' for r in rows)
        rows=[r for r in rows if r['dataset']!='wasm-obf-controls']
    pair_file=ROOT/'results/controls/wasmixer-pair-evidence.json'
    control_pairs=json.loads(pair_file.read_text()) if pair_file.exists() else {}
    parent_file=ROOT/'results/provenance/cryptic-bytes-parent-evidence.json'
    release_parents=json.loads(parent_file.read_text()) if parent_file.exists() else {}
    wasmizer_file=ROOT/'results/provenance/wasmizer-metadata.jsonl'
    wasmizer_metadata={r['sha256']:r for line in wasmizer_file.read_text().splitlines()
                      if (r:=json.loads(line))} if wasmizer_file.exists() else {}
    labels={r['sha256']:r['path'].split('/')[0] for r in rows if r['dataset']=='wasmmal' and r['path'].startswith(('malware/','benign/'))}
    prior={r['sha256'] for r in rows if r['dataset']=='wasmbench' or (r['dataset']=='swamped' and r['path'].startswith('experimental_data/'))}
    rows=[annotate(r,labels,prior,control_pairs,release_parents,wasmizer_metadata) for r in rows]
    unique={r['sha256']:r for r in rows if r.get('sha256')}
    features={}
    for i,(sha,r) in enumerate(unique.items()):
        file=CACHE/(sha+'.json')
        if not file.exists():
            features[sha]={'sha256':sha,'status':'pending'}; continue
        d=json.loads(file.read_text(encoding='utf-8'))
        if not (d.get('analyzer_version')==VERSION or (d.get('analyzer_version')=='2.0.0' and d['status']=='ok')):
            features[sha]={'sha256':sha,'status':'pending','reason':'stale_analyzer_version'}; continue
        flat={k:v for k,v in d.items() if not isinstance(v,(dict,list))}
        for op in ['br_table','call_indirect','call','loop','if','br','br_if','nop','i32.xor','i64.xor']:
            flat[op+'_count']=d.get('opcodes',{}).get(op,0) if d['status']=='ok' else None
        flat['imports_json']=json.dumps(d.get('imports',[]),ensure_ascii=True)
        flat['exports_json']=json.dumps(d.get('exports',[]),ensure_ascii=True)
        flat['opcodes_json']=json.dumps(d.get('opcodes',{}),ensure_ascii=True)
        features[sha]=flat
        if i%2000==0: print('read feature cache',i,'/',len(unique),flush=True)
    for r in rows:
        r['analysis_status']=features[r['sha256']]['status'] if r.get('sha256') else 'acquisition_failed_without_sha256'
    csv_write('occurrence-manifest.csv',rows)
    csv_write('module-features.csv',list(features.values()))
    groups=collections.defaultdict(list)
    for r in rows: groups[r['cohort']].append(r)
    summaries=[]
    for cohort,members in sorted(groups.items()):
        hashes={r['sha256'] for r in members if r.get('sha256')}
        ok=[features[s] for s in hashes if features[s]['status']=='ok']
        row={'cohort':cohort,'occurrences':len(members),'unique_sha256':len(hashes),
             'analyzed_ok':len(ok),'pending':sum(features[s]['status']=='pending' for s in hashes),
             'failed':sum(features[s]['status'] not in ('ok','pending') for s in hashes)}
        row['acquisition_failed_without_sha256']=sum(not r.get('sha256') for r in members)
        for key in ['name_section','br_table_count','call_indirect_count','nop_count','br_table_in_loop_count']:
            row[key+'_present']=sum(bool(f.get(key)) for f in ok)
        for key in ['bytes','defined_functions','instruction_count','max_br_table_targets','max_control_depth','code_section_entropy','data_section_entropy']:
            vals=[f[key] for f in ok if f.get(key) is not None]
            row[key+'_median']=statistics.median(vals) if vals else None
        row['unique_core_bytes']=len({f['core_bytes_sha256'] for f in ok})
        row['unique_code_payloads']=len({f['code_payload_sha256'] for f in ok})
        summaries.append(row)
    csv_write('cohort-summary.csv',summaries)
    datasets={d:{r['sha256'] for r in rows if r['dataset']==d and r.get('sha256')} for d in sorted({r['dataset'] for r in rows})}
    overlap=[{'dataset_a':a,'dataset_b':b,'unique_a':len(sa),'unique_b':len(sb),'shared_sha256':len(sa&sb)}
             for (a,sa),(b,sb) in itertools.combinations(datasets.items(),2)]
    csv_write('dataset-overlap.csv',overlap)
    split={part:{r['sha256'] for r in rows if r['dataset']=='wasmmal' and r['path'].startswith('Data_NewSplit/'+part+'/')} for part in ['train','test']}
    identities=[]
    for field in ['sha256','core_bytes_sha256','code_payload_sha256']:
        train={features[s].get(field) for s in split['train'] if features[s].get(field)}
        test={features[s].get(field) for s in split['test'] if features[s].get(field)}
        identities.append({'identity':field,'train_groups':len(train),'test_groups':len(test),
                           'shared_groups':len(train&test),'test_files_with_matching_train_identity':sum(features[s].get(field) in train for s in split['test'])})
    csv_write('wasmmal-split-identities.csv',identities)
    summary={'scope_status':'public_scope_snapshot_2026-10-06_analyzed',
             'datasets':len(datasets),'candidate_occurrences':len(rows),
             'occurrences_with_computed_sha256':sum(bool(r.get('sha256')) for r in rows),'unique_sha256':len(unique),
             'acquisition_failed_without_sha256':sum(not r.get('sha256') for r in rows),
             'historical_control_subset_copies_excluded':excluded_controls,
             'status_counts':dict(collections.Counter(f['status'] for f in features.values())),
             'note':'Counts concern current acquisition manifests. Failures without computed hash remain in the occurrence table; module features require a hash. Structural counts are not obfuscation prevalence.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__=='__main__': main()
