"""Download a fixed allowlist of detector source text, verify catalog Git blobs.

Does not import or run upstream code, load models, or execute target modules.
"""
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ('diversification2022', 'ASSERT-KTH/wasm_evasion', 'oracles/minos/minio.py'),
    ('diversification2022', 'ASSERT-KTH/wasm_evasion', 'oracles/minos/imaginator.py'),
    ('minerray', 'miner-ray/miner-ray.github.io', 'Parser/package.json'),
    ('wasim', 'WASimilarity/WASim', 'Classifier_Modules/requirements.txt'),
    ('wasim', 'WASimilarity/WASim', 'README.md'),
    ('wasim', 'WASimilarity/WASim', 'Classifier_Modules/neuralNetwork.h5'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/minos/src/minio.py'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/minos/src/minio_bulk.py'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/minos/main.py'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/minos/src/imaginator.py'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/minos/src/pandarize.py'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/minos/src/data_set_builder.py'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/minos/src/utils.py'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/minos/src/requirements.txt'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/minos/Dockerfile'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/miner-ray/src/package.json'),
    ('wasm-obf', 'hakonharnes/wasm-obf', 'detection/docker-compose.yml'),
]


def main():
    out = ROOT/'results/countermeasures/detector-feasibility'
    out.mkdir(exist_ok=True)
    records = []
    for name, repo, path in FILES:
        tree = json.loads((ROOT/'data/catalog'/name/'tree.json').read_text(encoding='utf-8'))
        entry = next(x for x in tree['tree'] if x['path'] == path)
        # The one .h5 entry is a tiny Git LFS pointer, not a neural model.
        assert entry['type'] == 'blob' and entry['size'] < 20000
        url = f'https://raw.githubusercontent.com/{repo}/{tree["sha"]}/{path}'
        target = out/(name+'-'+path.replace('/', '-'))
        if target.exists():
            data = target.read_bytes()
        else:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read(20001)
        assert len(data) == entry['size']
        blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert blob == entry['sha']
        data.decode('utf-8')
        target.write_bytes(data)
        records.append(dict(repository=repo, commit=tree['sha'], source_path=path, url=url,
                            git_blob_sha1=blob, sha256=hashlib.sha256(data).hexdigest(),
                            local_path=target.relative_to(ROOT).as_posix()))
    (out/'source-manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(f'Verified {len(records)} source text files; no upstream code executed')


if __name__ == '__main__':
    main()
