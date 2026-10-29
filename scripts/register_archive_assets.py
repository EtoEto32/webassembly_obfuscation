"""Register public archive assets from already pinned primary metadata."""
import json
from urllib.parse import quote
from acquire import ROOT


def main():
    path = ROOT/'experiments/archive-registry.json'
    entries = json.loads(path.read_text(encoding='utf-8'))
    by_id = {r['id']: r for r in entries}
    datasets = json.loads((ROOT/'experiments/dataset-registry.json').read_text())['datasets']
    for ds in datasets:
        if ds['id'] not in ('wbd', 'wobfuscator', 'seismic'):
            continue
        tree = json.loads((ROOT/'data/catalog'/ds['id']/'tree.json').read_text())
        if tree.get('truncated'):
            raise ValueError('Incomplete Git tree')
        for blob in tree['tree']:
            name = blob['path']
            if blob['type'] != 'blob' or not name.endswith(('.7z', '.zip', '.tar.xz', '.tar.bz2')):
                continue
            ident = ds['id']+'-'+name.replace('/', '-').replace('.', '-')
            by_id[ident] = {'id': ident, 'dataset': ds['id'],
                'filename': ds['id']+'-'+name.replace('/', '-'),
                'url': f'https://raw.githubusercontent.com/{ds["github"]}/{tree["sha"]}/{quote(name)}',
                'bytes': blob['size'], 'git_blob_sha1': blob['sha'],
                'commit': tree['sha'], 'repository_path': name,
                'role': 'archive inventory; corpus role must be established from contents'}
    release = json.loads((ROOT/'data/upstream/release.json').read_text())
    for asset in release['assets']:
        name = asset['name']
        ident = 'wasm-obf-'+name.replace('.', '-')
        by_id[ident] = {'id': ident, 'dataset': 'wasm-obf',
            'filename': 'wasm-obf-'+name, 'url': asset['browser_download_url'],
            'bytes': asset['size'], 'release': release['tag_name'],
            'asset_id': asset['id'], 'asset_name': name,
            'role': 'full controlled obfuscation release; optimized and unoptimized separate'}
    path.write_text(json.dumps(list(by_id.values()), indent=2)+'\n', encoding='utf-8')
    print('registered', len(by_id), 'archives')


if __name__ == '__main__':
    main()
