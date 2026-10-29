"""Join author .meta provenance to downloaded Wasm, without compiling projects."""
import hashlib
import json
import re
import zipfile
from pathlib import PurePosixPath
from acquire import ROOT
from analyze_corpus import acquired_rows


def main():
    archive=ROOT/'data/archives/wasmizer-msr2023-v2.zip'
    manifest=ROOT/'data/catalog/wasmizer-msr2023-archive/acquisition.jsonl'
    downloaded={r['path']:r for line in manifest.read_text().splitlines() if (r:=json.loads(line))}
    rows=[]
    with zipfile.ZipFile(archive) as z:
        names=set(z.namelist())
        for name in sorted(n for n in names if '/Dataset/wasm/' in n and n.endswith('.wasm')):
            r=downloaded[name]
            expected=PurePosixPath(name).stem
            if r['sha256'] != expected:
                raise ValueError('author filename SHA differs from acquired bytes: '+name)
            meta=name.removesuffix('.wasm')+'.meta'
            if meta not in names:
                rows.append({'sha256':r['sha256'],'path':name,'metadata_status':'missing'})
                continue
            raw=z.read(meta)
            sources=[s.strip() for s in raw.decode('utf-8').splitlines() if s.strip()]
            normalized=[s.removeprefix('./') for s in sources]
            # Preserve folder identifiers verbatim. Owner/repository hyphens are
            # ambiguous; neither GitHub URLs nor malware families are inferred.
            project_folders=sorted({s.split('/')[0] for s in normalized
                                    if '/' in s and not s.startswith(('dataset-wat/','dataset-wasm/'))})
            rows.append({'sha256':r['sha256'],'path':name,'metadata_status':'present',
                         'metadata_sha256':hashlib.sha256(raw).hexdigest(),
                         'source_paths':sources,'source_project_folders':project_folders,
                         'source_paths_count':len(sources),
                         'wat_source_path_evidence':any(s.lower().endswith('.wat') for s in normalized),
                         'test_path_evidence':any(re.search(r'(^|/)(test[^/]*|fixture[^/]*|spec)(/|$)',s,re.I) for s in normalized),
                         'dependency_path_evidence':any(re.search(r'(^|/)(third_party|dependencies|_deps|node_modules)(/|$)',s,re.I) for s in normalized),
                         'observed_date':'',
                         'date_basis':'December 2022 collection interval per artifact README; individual field-observation date unavailable'})
    out=ROOT/'results/provenance'; out.mkdir(parents=True,exist_ok=True)
    (out/'wasmizer-metadata.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    present=[r for r in rows if r['metadata_status']=='present']
    summary={'archive_sha256':json.loads(archive.with_suffix('.zip.receipt.json').read_text())['sha256'],
             'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
             'binary_records':len(rows),'metadata_present':len(present),'metadata_missing':len(rows)-len(present),
             'all_filename_hashes_match_acquired_bytes':True,
             'unique_source_project_folders':len({p for r in present for p in r['source_project_folders']}),
             'multiple_source_project_folders':sum(len(r['source_project_folders'])>1 for r in present),
             'wat_source_path_evidence':sum(r['wat_source_path_evidence'] for r in present),
             'test_path_evidence':sum(r['test_path_evidence'] for r in present),
             'dependency_path_evidence':sum(r['dependency_path_evidence'] for r in present),
             'individual_observation_dates_available':0,
             'interpretation':'Path indicators overlap and describe packaging, not maliciousness. Several binaries can share project folders; folders are not independent source programs or malware families.'}
    (out/'wasmizer-metadata-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    allrows=[r for r in acquired_rows() if r['dataset']!='wasm-obf-controls']
    wasmizer_hashes={r['sha256'] for r in rows}
    overlap=[]
    for dataset in sorted({r['dataset'] for r in allrows}-{'wasmizer'}):
        hashes={r['sha256'] for r in allrows if r['dataset']==dataset}
        overlap.append({'dataset':dataset,'unique_sha256':len(hashes),
                        'shared_with_wasmizer':len(hashes & wasmizer_hashes)})
    (out/'wasmizer-overlap.json').write_text(json.dumps(overlap,indent=2),encoding='utf-8')
    labels={r['sha256']:r['path'].split('/')[0] for r in allrows
            if r['dataset']=='wasmmal' and r['path'].startswith(('malware/','benign/'))}
    label_counts={label:sum(labels[s]==label for s in wasmizer_hashes & labels.keys())
                  for label in ('benign','malware')}
    (out/'wasmizer-wasmmal-label-overlap.json').write_text(json.dumps({
        'author_directory_labels':label_counts,'label_basis':'WasmMal root directory; no independent malware verdict'},indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    main()
