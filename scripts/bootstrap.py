"""Fetch pinned official tools and pinned upstream provenance sources."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import time
from acquire import ROOT, META, get, json_fetch

TOOLS = [
    ('wabt', '1.0.42', 'https://github.com/WebAssembly/wabt/releases/download/1.0.42/wabt-1.0.42-windows-x64.tar.gz'),
    ('binaryen', '133', 'https://github.com/WebAssembly/binaryen/releases/download/version_133/binaryen-version_133-x86_64-windows.tar.gz'),
]

def main():
    target = ROOT / '.tools'
    target.mkdir(exist_ok=True)
    records = []
    for name, version, url in TOOLS:
        path = target / url.rsplit('/', 1)[-1]
        if not path.exists():
            with get(url) as response, path.open('wb') as output:
                shutil.copyfileobj(response, output)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with get(url + '.sha256') as response:
            checksum_text = response.read().decode().strip()
        if checksum_text.split()[0] != digest:
            raise RuntimeError('Official checksum mismatch for ' + name)
        with tarfile.open(path) as archive:
            archive.extractall(target, filter='data')
        records.append({'tool': name, 'version': version, 'url': url, 'sha256': digest, 'official_checksum': checksum_text})
        print(name, version, digest, flush=True)
    META.mkdir(parents=True, exist_ok=True)
    (META / 'tool-downloads.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    tree = json_fetch('https://api.github.com/repos/HakonHarnes/wasm-obf/git/trees/main?recursive=1', 'tree.json')
    commit = tree['sha']
    chosen = []
    for entry in tree['tree']:
        path = entry['path']
        if entry['type'] != 'blob': continue
        if path in ['README.md', 'dataset/main.py', 'dataset/Dockerfile', 'dataset/docker-compose.yml', 'obfuscation/tigress/main.py', 'obfuscation/tigress/Dockerfile', 'optimization/opt/main.py', 'optimization/opt/Dockerfile']:
            chosen.append(path)
        elif path.startswith(('dataset/utilities/', 'dataset/games/')) and (path.endswith('/build.sh') or path.endswith('/main.c') or path.endswith('/flatten.sh')):
            chosen.append(path)
    provenance = []
    for path in chosen:
        url = f'https://raw.githubusercontent.com/HakonHarnes/wasm-obf/{commit}/{path}'
        dest = META / 'source' / path
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            with get(url) as response:
                dest.write_bytes(response.read())
        provenance.append({'path': path, 'commit': commit, 'url': url, 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
    (META / 'source-manifest.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    print('provenance files', len(provenance))

if __name__ == '__main__': main()
