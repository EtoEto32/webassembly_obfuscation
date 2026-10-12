"""Inventory license declarations in fixed primary metadata, without legal inference.

A repository license is not automatically a license for every third-party binary.
"""
import datetime
import hashlib
import json
import re
from analyze_corpus import ROOT


def evidence(path):
    raw=path.read_bytes()
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()}


def main():
    registry=json.loads((ROOT/'experiments/dataset-registry.json').read_text(encoding='utf-8'))
    acquired={r['dataset'] for r in json.loads((ROOT/'results/corpus/acquisition-checkpoint.json').read_text(encoding='utf-8'))['datasets']}
    rows=[]
    for dataset in registry['datasets']:
        name=dataset['id'];base=ROOT/'data/catalog'/name
        row={'dataset':name,'binaries_acquired':name in acquired,'evidence':[],
             'repository_license_declaration':None,'artifact_license_declaration':None,
             'third_party_binary_rights_independently_confirmed':False}
        tree_path=base/'tree.json'
        if tree_path.exists():
            tree=json.loads(tree_path.read_text(encoding='utf-8'));row['evidence'].append(evidence(tree_path))
            row['commit']=tree['sha'];row['tree_truncated']=tree.get('truncated',False)
            names=[r['path'] for r in tree['tree'] if r.get('type')=='blob' and
                   re.search(r'(^|/)(licen[sc]e|copying)([./_-]|$)',r['path'],re.I)]
            row['license_named_paths']=names
            root=[n for n in names if '/' not in n]
            row['root_license_path_present']=bool(root)
            for n in root:
                paths=[base/n,base/'supporting'/n]
                path=next((p for p in paths if p.exists()),None)
                if path:
                    row['evidence'].append(evidence(path));text=path.read_text(encoding='utf-8')
                    row['repository_license_declaration']='MIT' if 'Permission is hereby granted, free of charge' in text else 'Apache-2.0' if 'Apache License' in text and 'Version 2.0' in text else 'text_requires_review'
            if not root:row['repository_license_status']='No root license-named file found in pinned tree; nested declarations do not establish corpus-wide terms'
        if name in ('androwasm','proof-of-theft'):
            path=base/'record.json';record=json.loads(path.read_text(encoding='utf-8'))
            row['evidence'].append(evidence(path));row['artifact_license_declaration']=record['metadata'].get('license')
            row['artifact_record_url']=record['links']['self_html']
            if name=='proof-of-theft':
                description=base/'artifact-description.txt'
                if description.exists():
                    text=description.read_text(encoding='utf-8')
                    if 'GPL version 2' not in text:raise ValueError('Review artifact license wording')
                    row['evidence'].append(evidence(description))
                    row['artifact_description_license_declaration']='GPL version 2, section 5'
                    row['declaration_difference']='Zenodo record says CC-BY-4.0, while artifact description section 5 says GPL version 2; applicability is not resolved by this audit.'
        if name=='wasmizer':
            path=ROOT/'data/catalog/followup-sources/wasmizer-figshare.json';record=json.loads(path.read_text(encoding='utf-8'))
            row['evidence'].append(evidence(path));row['artifact_license_declaration']=record.get('license')
            row['artifact_record_url']=record['url_public_html']
        if name=='wasmbench':
            row['evidence'].append(evidence(base/'README.md'))
            row['scope_note']='README limits MIT to authors own crawling/analysis code and disclaims ownership of collected binaries; research redistribution statement is not per-binary third-party license verification.'
        elif name=='industry2025':
            row['evidence'].append(evidence(ROOT/'data/catalog/industry2025-validwasm-archive/inventory.json'))
            row['scope_note']='Public author archive contains binary files only; no archive-wide license declaration found in downloaded members.'
        elif name not in acquired:
            row['scope_note']='No existing public binary corpus acquired in this pilot; availability reasons are in the dataset registry.'
        else:
            row['scope_note']='Declarations recorded at repository/artifact level; applicability to each included third-party binary not independently established.'
        rows.append(row)
    output={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'method':'Read fixed repository trees and available root license texts, author README and archive record metadata. Presence/absence is limited to these inspected sources.',
            'datasets':rows,'scope_limit':'A declaration inventory, not a legal permission determination or an assertion that a missing license means public domain.',
            'delivery':'Research outputs are code, measurements, hashes and source links. Downloaded third-party binary objects remain local data, excluded from source control.'}
    path=ROOT/'results/catalog/license-metadata-audit.json'
    path.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps({'candidate_records':len(rows),'acquired_records':sum(r['binaries_acquired'] for r in rows),
                      'output':path.relative_to(ROOT).as_posix()}),flush=True)


if __name__=='__main__':main()
