"""Compare two saved runs and record dependencies; no experimental measurements."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    first, second = [Path(p).resolve() for p in sys.argv[1:3]]
    manifests = [json.loads((p / 'manifest.json').read_text()) for p in (first, second)]
    checks = [json.loads((p / 'checks.json').read_text()) for p in (first, second)]
    maps = [{a['file']: a['sha256'] for a in m['artifacts']} for m in manifests]
    assert maps[0] == maps[1] and len(maps[0]) == 33
    for directory, manifest, check in zip((first, second), manifests, checks):
        for artifact in manifest['artifacts']:
            assert digest(directory / artifact['file']) == artifact['sha256']
        assert len(check['rows']) == 33
        assert sum(r['cases'] for r in check['rows']) == 35376
        assert sum(r['mismatches'] for r in check['rows']) == 0
        assert len(manifest['attacks']) == 9
        assert all(a['status'] == 'recovered' and a['execution_queries'] == 0 for a in manifest['attacks'])
        assert len(manifest['negative_controls']) == 6
        assert all(n['status'] == 'rejected' for n in manifest['negative_controls'])
    dependencies = [
        'research/table-transport/probe.py', 'research/table-transport/check.cjs',
        'research/observation-synthesis/transform.py',
        '.tools/wabt-1.0.42/bin/wasm2wat.exe', '.tools/wabt-1.0.42/bin/wat2wasm.exe',
        '.tools/wabt-1.0.42/bin/wasm-validate.exe',
        '.tools/binaryen-version_133/bin/wasm-opt.exe',
    ]
    result = {'runs': [str(p.relative_to(ROOT)) for p in (first, second)],
              'matching_binary_hashes': 33, 'cases_per_run': 35376,
              'mismatches_per_run': [0, 0], 'recovered_targets_per_run': [9, 9],
              'dependencies': {p: digest(ROOT / p) for p in dependencies}}
    with (second / 'reproduction-audit.json').open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    # Preserve shared parser source for inspection alongside the experiment scripts.
    with (second / 'shared-transform.py').open('xb') as f:
        f.write((ROOT / dependencies[2]).read_bytes())
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
