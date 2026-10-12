"""Verify existing objects and read cached ABI metadata; never execute Wasm."""
import collections
import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/runtime-mining'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (ROOT / 'results/mining-methods/input-manifest.csv').open(encoding='utf-8') as h:
        inputs = [r for r in csv.DictReader(h) if r['method'] != 'wasm-mutate/iteration-series']
    records = []
    for row in inputs:
        obj = ROOT / row['object']
        digest = hashlib.sha256(obj.read_bytes()).hexdigest()
        if digest != row['sha256']:
            raise ValueError('Object differs from provenance: ' + row['object'])
        meta = json.loads((ROOT / 'data/analysis-v2' / (digest + '.json')).read_text())
        records.append(dict(**row, imports=meta.get('imports'), exports=meta.get('exports'),
                            execution_status='not run', abi_status='host adapter not confirmed'))
    repo = ROOT / 'data/upstream/wasm_evasion'
    prefix = 'malware_reproduction/rq3/replace_experiments/'
    listing = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '-r', '--name-only',
                                       '6e41bb3fa0f9d06619758709094b0e2a13beb593', prefix], text=True).splitlines()
    summary = dict(status='static inventory only; not mining results', objects_verified=len(records),
                   programs=sorted({r['program'] for r in records}),
                   methods=sorted({r['method'] for r in records}),
                   source_commit='6e41bb3fa0f9d06619758709094b0e2a13beb593',
                   upstream_wasm_files=[s for s in listing if s.endswith('.wasm')],
                   upstream_wat_count=sum(s.endswith('.wat') for s in listing),
                   counts_by_release=dict(collections.Counter(r['release'] for r in records)),
                   limitations=['The source tree includes WAT, but no .wasm files in this experiment directory.',
                                'Compiling WAT would be reconstruction, not proof of original binary identity.',
                                'Cryptic Bytes hash_cn ABI differs from CoinHive cryptonight_hash ABI.',
                                'User has no mining payout address yet.'])
    paper_originals = []
    for prefix_id in ('d2141ff2', 'a32a6f4b', '046dc081', 'fbdd1efa', '0d996462', '006b2fb6'):
        matches = list((ROOT / 'data/objects').glob(prefix_id + '*.bin'))
        if len(matches) != 1:
            raise ValueError('Original object missing or ambiguous: ' + prefix_id)
        obj = matches[0]
        sha = hashlib.sha256(obj.read_bytes()).hexdigest()
        if sha != obj.stem:
            raise ValueError('Original object digest mismatch')
        meta = json.loads((ROOT / 'data/analysis-v2' / (sha + '.json')).read_text())
        paper_originals.append(dict(paper_id=prefix_id, sha256=sha, object=str(obj.relative_to(ROOT)),
                                    imports=meta.get('imports'), exports=meta.get('exports'),
                                    execution_status='not run'))
    summary['paper_original_objects_verified'] = len(paper_originals)
    summary['paper_variants_status'] = 'WAT distribution identified; original binary provenance not yet matched'
    (OUT / 'paper-original-manifest.json').write_text(json.dumps(paper_originals, indent=2), encoding='utf-8')
    source_paths = ('dataset/miners/cn-0/main.c', 'dataset/miners/cn-0/build.sh',
                    'miner/client/src/worker.js', 'miner/client/src/cn-0.js', 'miner/server/pools.json')
    receipts = []
    for path in source_paths:
        obj = ROOT / 'data/upstream/source' / path
        if obj.exists():
            receipts.append(dict(path=path, commit='009e9e7bd812cbecacb506507e36834ae3ecddc4',
                                 url='https://raw.githubusercontent.com/HakonHarnes/wasm-obf/009e9e7bd812cbecacb506507e36834ae3ecddc4/' + path,
                                 sha256=hashlib.sha256(obj.read_bytes()).hexdigest()))
    (OUT / 'additional-source-receipts.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
    (OUT / 'input-abi-inventory.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    (OUT / 'input-inventory-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
