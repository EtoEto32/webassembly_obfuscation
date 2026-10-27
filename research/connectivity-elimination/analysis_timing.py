"""Comparable symbolic-analysis timing; not a new attack or independent oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import time
import prototype as p
import recover as r

ap = argparse.ArgumentParser()
ap.add_argument('directory', type=Path)
a = ap.parse_args()
build = json.loads((a.directory / 'build.json').read_text())
prior = {x['file']: x for x in json.loads((a.directory / 'recovery-v2.json').read_text())['results']}
rows = list(build['conditions'])
random.Random(0x53434f50).shuffle(rows)
results = []
for row in rows:
    src = a.directory / row['file']
    binary = src.read_bytes()
    mod = p.parse(p.tool('wasm2wat', [src, '--fold-exprs']))
    samples = []
    for _ in range(3):
        bdd = r.BDD()
        start = time.perf_counter()
        image = r.initial_memory(binary)
        if image:
            n, root, extra = r.graph_root(image, bdd)
        else:
            n, root, extra = r.plain_root(src, bdd, mod)
        samples.append(time.perf_counter() - start)
        assert bdd.digest(root) == prior[row['file']]['normalized_sha256']
    results.append({**row, 'samples_seconds': samples, 'median_seconds': statistics.median(samples),
                    'normalized_sha256': bdd.digest(root), 'allocated_nodes': len(bdd.nodes)})
with (a.directory / 'analysis-timing.json').open('x', encoding='utf-8') as f:
    json.dump({'scope': 'Both families: memory/body model and BDD. Excludes WABT disassembly and output compilation. Three same-process samples, no significance claim.',
               'results': results}, f, indent=2)
for name in ('analysis_timing.py', 'recover.py'):
    (a.directory / ('timing-source-' + name)).write_bytes(Path(__file__).with_name(name).read_bytes())
print(json.dumps({'conditions': len(results), 'canonical_hash_mismatches': 0}))
