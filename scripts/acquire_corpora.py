"""Fetch pinned public corpus archives; verify every .wasm against its Git blob.

Files are treated only as bytes. No upstream programs or sample modules run.
Content-addressed .bin storage avoids expanding duplicate repository copies.
"""
import argparse
import datetime
import hashlib
import json
import tarfile
import time
from pathlib import Path
from acquire import ROOT, get

CACHE = ROOT / 'data' / 'catalog'
OBJECTS = ROOT / 'data' / 'objects'


def acquire(dataset):
    cache = CACHE / dataset['id']
    tree = json.loads((cache / 'tree.json').read_text(encoding='utf-8'))
    if tree.get('truncated'):
        raise ValueError('Refusing an incomplete tree')
    all_blobs = {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
    prefixes=dataset.get('wasm_include_prefixes')
    scope=lambda p:not prefixes or any(p.startswith(prefix) for prefix in prefixes)
    expected = {p: x for p, x in all_blobs.items() if p.lower().endswith('.wasm')
                or p in ('Data_NewSplit/train.csv', 'Data_NewSplit/test.csv')}
    expected={p:x for p,x in expected.items() if scope(p)}
    url = f'https://codeload.github.com/{dataset["github"]}/tar.gz/{tree["sha"]}'
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    OBJECTS.mkdir(parents=True, exist_ok=True)
    manifest = cache / 'acquisition.jsonl'
    temporary = manifest.with_suffix('.jsonl.partial')
    rows, seen, last = [], set(), time.monotonic()
    stored = {}
    print(f'{dataset["id"]}: fetching pinned archive ({len(expected)} selected paths)', flush=True)
    with get(url) as response, tarfile.open(fileobj=response, mode='r|gz') as archive, temporary.open('w', encoding='utf-8') as out:
        for member in archive:
            path = member.name.partition('/')[2]
            if path not in all_blobs or not member.isfile() or not scope(path):
                continue
            source = archive.extractfile(member)
            prefix = source.read(8)
            # Several research artifacts store binaries under extensionless
            # SHA names. Inspect magic in every regular repository member.
            if path not in expected and prefix[:4] != b'\0asm':
                continue
            expected[path] = all_blobs[path]
            if path in seen or member.size != expected[path]['size']:
                raise ValueError(f'Unexpected member: {path}')
            data = prefix + source.read()
            git_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if git_blob != expected[path]['sha']:
                raise ValueError(f'Git blob mismatch: {path}')
            sha256 = hashlib.sha256(data).hexdigest()
            dest = OBJECTS / (sha256 + '.bin')
            if sha256 not in stored:
                try:
                    if not dest.exists():
                        dest.write_bytes(data)
                    if hashlib.sha256(dest.read_bytes()).hexdigest() != sha256:
                        raise ValueError('Corrupt cached object: ' + sha256)
                    stored[sha256] = ('stored_verified', None)
                except OSError as exc:
                    # Do not bypass OS protection/quarantine. Record this file
                    # and continue the corpus; downloaded bytes were hashed.
                    stored[sha256] = ('local_io_failed', str(exc))
            row = {'dataset': dataset['id'], 'commit': tree['sha'], 'path': path,
                   'bytes': len(data), 'git_blob': git_blob, 'sha256': sha256,
                   'wasm_magic': data[:4] == b'\0asm',
                   'lfs_pointer': data.startswith(b'version https://git-lfs.github.com/spec/v1'),
                   'object': dest.relative_to(ROOT).as_posix(),
                   'acquisition_status': stored[sha256][0],
                   'acquisition_error': stored[sha256][1]}
            rows.append(row); seen.add(path)
            out.write(json.dumps(row) + '\n')
            if time.monotonic() - last > 20:
                print(f'{dataset["id"]}: verified {len(rows)}/{len(expected)} paths', flush=True)
                out.flush(); last = time.monotonic()
    missing = set(expected) - seen
    if missing:
        raise ValueError(f'Missing {len(missing)} expected members')
    temporary.replace(manifest)
    wasm = [r for r in rows if r['path'].lower().endswith('.wasm') or r['wasm_magic']]
    summary = {'dataset': dataset['id'], 'commit': tree['sha'], 'archive_url': url,
               'started_utc': started, 'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'wasm_paths': len(wasm), 'unique_sha256': len({r['sha256'] for r in wasm}),
               'magic_paths': sum(r['wasm_magic'] for r in wasm),
               'lfs_pointer_paths': sum(r['lfs_pointer'] for r in wasm), 'missing_paths': len(missing),
               'local_io_failed_paths': sum(r['acquisition_status'] != 'stored_verified' for r in wasm)}
    summary['scan_scope'] = 'all regular Git-tree members inspected for Wasm magic; .wasm paths retained even if invalid; archive interiors and JS embeddings excluded'
    if prefixes:
        summary['scan_scope']='Every regular Git-tree member under the explicit author-benchmark prefixes inspected for Wasm magic; tool fixtures outside this adopted dataset scope excluded'
        summary['included_prefixes']=prefixes
        summary['wasm_paths_outside_adopted_scope']=sum(p.lower().endswith('.wasm') and not scope(p) for p in all_blobs)
    (cache / 'acquisition-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('datasets', nargs='+')
    args = parser.parse_args()
    registry = json.loads((ROOT / 'experiments/dataset-registry.json').read_text(encoding='utf-8'))
    by_id = {d['id']: d for d in registry['datasets']}
    for ident in args.datasets:
        acquire(by_id[ident])
