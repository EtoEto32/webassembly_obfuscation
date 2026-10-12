"""Audit public GitHub corpus layouts without executing repository code."""
import concurrent.futures
import collections
import csv
import datetime
import json
from pathlib import Path
import urllib.error
from acquire import ROOT, get

CACHE = ROOT / 'data' / 'catalog'
OUT = ROOT / 'results' / 'catalog'

def fetch(url, destination):
    if not destination.exists():
        with get(url) as response:
            data = response.read()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return json.loads(destination.read_text(encoding='utf-8'))

def audit(dataset):
    repo = dataset['github']
    cache = CACHE / dataset['id']
    info = fetch(f'https://api.github.com/repos/{repo}', cache / 'repository.json')
    revision=dataset.get('ref',info['default_branch'])
    tree = fetch(f'https://api.github.com/repos/{repo}/git/trees/{revision}?recursive=1', cache / 'tree.json')
    blobs = [x for x in tree['tree'] if x['type'] == 'blob']
    wasm = [x for x in blobs if x['path'].lower().endswith('.wasm')]
    archive = [x for x in blobs if x['path'].lower().endswith(('.zip', '.7z', '.tar.gz', '.tgz', '.rar', '.tar.xz', '.tar.bz2', '.tar', '.apk'))]
    readmes = [x for x in blobs if x['path'].lower() == 'readme.md']
    for item in readmes:
        dest = cache / 'README.md'
        if not dest.exists():
            with get(f'https://raw.githubusercontent.com/{repo}/{tree["sha"]}/{item["path"]}') as response:
                dest.write_bytes(response.read())
    row = {
        'dataset': dataset['id'], 'repository': repo, 'commit': tree['sha'],
        'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'tree_truncated': tree.get('truncated', False),
        'repository_blob_files': len(blobs), 'wasm_path_count': len(wasm),
        'unique_wasm_git_blob_ids': len({x['sha'] for x in wasm}),
        'wasm_path_bytes': sum(x.get('size', 0) for x in wasm),
        'archive_path_count': len(archive), 'archive_bytes': sum(x.get('size',0) for x in archive),
        'readme_available': bool(readmes),
        'note': 'Tree-level inventory only; archives/releases and embedded Wasm not counted as binaries; Git blob identity is not a downloaded SHA-256 audit.'
    }
    details = {'summary': row, 'archives': archive, 'wasm_by_top_directory': dict(collections.Counter(x['path'].split('/')[0] for x in wasm)), 'metadata_candidates': [x['path'] for x in blobs if x['path'].lower().endswith(('.csv','.json','.jsonl','.tsv'))][:100]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'{dataset["id"]}-layout.json').write_text(json.dumps(details, indent=2), encoding='utf-8')
    return row

def main():
    registry = json.loads((ROOT / 'experiments/dataset-registry.json').read_text(encoding='utf-8'))
    datasets = [x for x in registry['datasets'] if x.get('github')]
    rows, failures = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(audit, x): x for x in datasets}
        for future in concurrent.futures.as_completed(futures):
            dataset = futures[future]
            try:
                row = future.result()
                rows.append(row)
                print(json.dumps(row), flush=True)
            except Exception as exc:
                failures.append({'dataset': dataset['id'], 'error': repr(exc)})
                print(dataset['id'], repr(exc), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda x:x['dataset'])
    if rows:
        with (OUT / 'repository-inventory.csv').open('w', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    (OUT / 'failures.json').write_text(json.dumps(failures, indent=2), encoding='utf-8')

if __name__ == '__main__': main()
