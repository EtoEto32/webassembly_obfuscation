"""Audit date-field availability in explicitly listed public metadata snapshots."""
import collections
import csv
import hashlib
import json
from analyze_corpus import ROOT, acquired_rows


def main():
    source=ROOT/'data/extracted/wasmbench-filtered/filtered.pretty.json'
    data=json.loads(source.read_text())
    acquired={r['sha256'] for r in acquired_rows(['wasmbench'])}
    files=[f for r in data.values() for f in r.get('files',[])]
    fields=collections.Counter(k for f in files for k in f)
    date_fields=[k for k in fields if any(s in k.lower() for s in ('date','time','observ','crawl'))]
    other=ROOT/'data/catalog/wasmbench/dataset-metadata/filtered.pretty.json'
    metadata=ROOT/'results/provenance/wasmizer-metadata-summary.json'
    wasmizer=json.loads(metadata.read_text())
    wm_rows=[json.loads(line) for line in (ROOT/'data/catalog/wasmmal/acquisition.jsonl').read_text().splitlines()]
    wm_csv=[]
    for split in ('train','test'):
        r=next(r for r in wm_rows if r['path']=='Data_NewSplit/'+split+'.csv')
        path=ROOT/r['object'];raw=path.read_bytes()
        rows=list(csv.reader(raw.decode('utf-8-sig').splitlines()))
        valid=all(len(row)==2 and row[0].endswith('.wasm') and row[1] in ('0','1') for row in rows)
        if not valid:raise ValueError('Unexpected WasmMal label CSV schema')
        wm_csv.append({'source_path':r['path'],'rows_without_header':len(rows),
                       'schema':'filename, integer author label; no header',
                       'sha256':hashlib.sha256(raw).hexdigest(),'observation_date_column':False})
    miner_csv=[]
    for path in sorted((ROOT/'data/catalog/minerray/supporting/Data').glob('*.csv')):
        raw=path.read_bytes();rows=list(csv.reader(raw.decode('utf-8-sig').splitlines()))
        miner_csv.append({'metadata_path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),
                          'data_rows':len(rows)-1,'columns':rows[0],
                          'interpretation':'Site-level context; no observation-date or binary-SHA column in inspected header'})
    if len(miner_csv)!=2:raise ValueError('Run fetch_supporting_metadata.py before this audit')
    industry_path=ROOT/'data/catalog/industry2025-validwasm-archive/inventory.json'
    industry=json.loads(industry_path.read_text())
    minesweeper_path=ROOT/'results/provenance/minesweeper-crawled-summary.json'
    minesweeper=json.loads(minesweeper_path.read_text())
    if not all(r['path'].lower().endswith('.wasm') for r in industry):raise ValueError('Review new non-Wasm archive content')
    result={'scope':'WasmBench filtered v1.0, Wasmizer Figshare v2, WasmMal label CSVs, two MinerRay site CSVs, Industry2025 downloaded archive, and the complete downloaded MineSweeper crawled-site archive; not a claim about every metadata source on the Web',
            'wasmbench':{'metadata_path':source.relative_to(ROOT).as_posix(),
                        'metadata_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                        'module_records':len(data),'source_file_records':len(files),
                        'acquired_sha_covered':len(acquired & data.keys()),'acquired_sha_uncovered':len(acquired-data.keys()),
                        'source_file_field_counts':dict(fields),'potential_date_field_names':date_fields,
                        'same_parsed_content_as_git_metadata':data==json.loads(other.read_text()),
                        'interpretation':'No per-source observation date field found' if not date_fields else 'Date field semantics require individual review'},
            'wasmizer':{'metadata_audit_path':metadata.relative_to(ROOT).as_posix(),
                        'metadata_audit_sha256':hashlib.sha256(metadata.read_bytes()).hexdigest(),
                        'records':wasmizer['binary_records'],
                        'individual_observation_dates_available':wasmizer['individual_observation_dates_available'],
                        'collection_interval':'2022-12 per author artifact README',
                        'interpretation':'Collection interval is not a per-binary field observation or first appearance date'},
            'wasmmal':{'label_csvs':wm_csv,'interpretation':'Label/split files provide no individual observation dates or verified mutation-parent dates'},
            'minerray':{'site_csvs':miner_csv,'interpretation':'Named site samples are not hash-linked per-binary temporal measurements'},
            'industry2025':{'inventory_path':industry_path.relative_to(ROOT).as_posix(),
                            'inventory_sha256':hashlib.sha256(industry_path.read_bytes()).hexdigest(),
                            'archive_regular_members':len(industry),'all_members_are_wasm':True,
                            'interpretation':'Downloaded archive has binaries only; external urlscan/archive observations were not reconstructed and ZIP/7z modification times are not used as field observation dates'},
            'minesweeper':{'audit_path':minesweeper_path.relative_to(ROOT).as_posix(),
                           'audit_sha256':hashlib.sha256(minesweeper_path.read_bytes()).hexdigest(),
                           'crawl_interval':minesweeper['paper_evidence']['crawl_interval'],
                           'drive_by_mining_websites':minesweeper['paper_evidence']['drive_by_mining_websites'],
                           'archive_core_wasm_occurrences':minesweeper['core_wasm_occurrences'],
                           'archive_unique_core_wasm_sha256':minesweeper['unique_core_wasm_sha256'],
                           'interpretation':'Paper-supported corpus observation interval; no per-SHA first-seen date and no second comparable interval in this artifact'},
            'conclusion':'MineSweeper supports one corpus-level March 2018 observation interval. The inspected metadata still cannot support an individual-binary temporal obfuscation trend or a cross-period trend. Publication/download dates are not used as attack dates.'}
    (ROOT/'results/provenance/observation-dates-partial.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    main()
