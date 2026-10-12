"""Locate acquired mining candidates and their runtime interfaces; execute nothing."""
import collections
import csv
import json
from pathlib import Path
from analyze_corpus import acquired_rows

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/runtime-mining/cross-dataset'
HASH_EXPORTS = {'hash_cn', '_hash_cn', 'cryptonight_hash', '_cryptonight_hash'}


def interface_metadata(source):
    # Cached analyzer JSON also contains long per-function instruction lists.
    # Interfaces precede those lists; decode only complete header fields.
    with source.open(encoding='utf-8') as handle:
        header = handle.read(65536)
    decoder = json.JSONDecoder()
    result = {}
    for name in ('imports', 'exports', 'bytes', 'code_section_bytes', 'core_bytes_sha256'):
        marker = '"' + name + '":'
        position = header.find(marker)
        if position >= 0:
            try:
                result[name] = decoder.raw_decode(header[position + len(marker):].lstrip())[0]
            except ValueError:
                pass
    # Per-function instruction_count fields also occur in the header. The
    # corpus-wide total is a trailing root field, so never take the first match.
    with source.open('rb') as handle:
        handle.seek(max(0, source.stat().st_size - 65536))
        tail = handle.read().decode('utf-8', errors='replace')
    marker = '"instruction_count":'
    position = tail.rfind(marker)
    if position >= 0:
        result['instruction_count'] = decoder.raw_decode(tail[position + len(marker):].lstrip())[0]
    if 'imports' not in result or 'exports' not in result or 'instruction_count' not in result:
        complete = json.loads(source.read_text(encoding='utf-8'))
        for name in ('imports', 'exports', 'instruction_count'):
            result[name] = complete.get(name, []) if name != 'instruction_count' else complete.get(name)
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metadata = {}
    records = []
    for row in acquired_rows():
        dataset, path, sha = row['dataset'], row['path'], row.get('sha256')
        lower = path.lower()
        declared = (
            dataset == 'minesweeper' and '/miner_samples/' in '/' + lower
            or dataset == 'swamped' and 'cryptojackers_43' in lower
            or dataset == 'proof-of-theft' and any(x in lower for x in
                ('___obfuscated_miners/', 'cryptonight', 'webminerpoolhashcn', '/xmr', 'miner_bit', 'miner_eth'))
            or dataset == 'deepminer'
            or dataset == 'seismic' and 'cryptonight' in lower
            or dataset == 'wasm-obf' and any(x in lower for x in ('/cn-', '/cn_')))
        # Inspect other source interfaces too: author malware labels alone
        # never establish mining or algorithm compatibility.
        if not declared and dataset not in ('minerray', 'minesweeper', 'swamped',
                'proof-of-theft', 'seismic', 'wasim', 'diversification2022'):
            continue
        if sha not in metadata:
            source = ROOT / 'data/analysis-v2' / (str(sha) + '.json')
            metadata[sha] = interface_metadata(source) if source.exists() else {}
        meta = metadata[sha]
        exports = [e['name'] for e in meta.get('exports', [])]
        hash_exports = sorted(set(exports) & HASH_EXPORTS)
        if not declared and not hash_exports:
            continue
        imports = meta.get('imports', [])
        role = 'candidate; source/ABI/algorithm not yet verified'
        if lower.endswith('.o'):
            role = 'intermediate object; excluded from final-program measurement'
        elif lower.endswith('.orig.wasm'):
            role = 'original filename marker; pairing still needs source evidence'
        if any(i['module'] not in ('env', 'wasi_snapshot_preview1') for i in imports):
            role += '; nonstandard imports require instrumentation/host review'
        records.append(dict(dataset=dataset, path=path, sha256=sha,
            object=row.get('object', ''), origin=row.get('archive_url', row.get('url', '')),
            acquisition_status=row.get('acquisition_status'), role=role,
            mining_basis='source cohort/path declaration' if declared else 'named hash export candidate only',
            hash_exports=';'.join(hash_exports), exports=';'.join(exports),
            imports=';'.join(i['module'] + '.' + i['name'] for i in imports),
            algorithm='unconfirmed', runtime_status='not measured',
            bytes=meta.get('bytes'), instruction_count=meta.get('instruction_count'),
            code_section_bytes=meta.get('code_section_bytes'),
            core_bytes_sha256=meta.get('core_bytes_sha256')))
    # Keep all provenance occurrences, while deduplicating only execution work.
    with (OUT / 'mining-candidates.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    groups = collections.defaultdict(list)
    for row in records:
        groups[row['dataset']].append(row)
    report = dict(scope='Acquired public corpus; candidate inventory, not executed or confirmed miners',
        datasets={key:dict(occurrences=len(rows), unique_inputs=len({r['sha256'] for r in rows}),
            named_hash_export_inputs=len({r['sha256'] for r in rows if r['hash_exports']}))
            for key, rows in sorted(groups.items())},
        total_unique_candidates=len({r['sha256'] for r in records}),
        measured_baseline='results/runtime-mining/runs/cn-pico-normal-binaries-20261007-222952/summary.json',
        limitations=['General-purpose and malware-only corpora without mining provenance are not yet execution candidates.',
            'Interfaces missing from the first 64KiB of cache require a separate full interface audit.',
            'Named exports and source labels do not establish mining correctness or malicious use.',
            'Directory entries are not necessarily final uninstrumented programs.',
            'Algorithm/ABI and original/variant pairing must be verified before execution.',
            'Missing public artifacts and invalid modules remain coverage gaps.',
            'Cross-dataset coverage alone is not a novelty claim.'])
    (OUT / 'inventory-summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
