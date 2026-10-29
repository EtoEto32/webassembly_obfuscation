"""Audit existing evidence and the limited polynomial learner; do not overwrite runs."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import shutil
from blackbox import learn
from probe import value


def run(wasm_root, destination):
    destination.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((wasm_root/'manifest.json').read_text())
    checks = json.loads((wasm_root/'checks.json').read_text())
    bb_manifest = json.loads((wasm_root/'blackbox/manifest.json').read_text())
    bb_checks = json.loads((wasm_root/'blackbox/checks.json').read_text())
    assert checks['conditions'] == len(manifest['rows']) == 54
    assert checks['executions'] == 14256 and checks['mismatches'] == 0
    assert bb_checks['conditions'] == len(bb_manifest['rows']) == 18
    assert bb_checks['executions'] == 4752 and bb_checks['mismatches'] == 0
    for r in manifest['rows']:
        b = (wasm_root/r['wasm']).read_bytes()
        assert hashlib.sha256(b).hexdigest() == r['sha256'] and len(b) == r['bytes']
    source_matches = {}
    for name, old in [('probe.py', 'source/probe.py'),
                      ('wasm_gate.py', 'source/wasm_gate.py'),
                      ('blackbox.py', 'blackbox/blackbox.py')]:
        source_matches[name] = Path(__file__).with_name(name).read_bytes() == (wasm_root/old).read_bytes()
    assert all(source_matches.values())
    # Exhaust all degree <= 4 coefficient lists over Z/8, independently of the
    # narrower quadratic-composition examples used to generate the Wasm fixtures.
    cases = comparisons = 0
    for p in itertools.product(range(8), repeat=5):
        q, _ = learn([value(p, x, 8) for x in range(5)], bits=3)
        cases += 1
        for x in range(8):
            assert value(p, x, 8) == value(q, x, 8)
            comparisons += 1
    rng = random.Random(2026101805)
    random_comparisons = 0
    for _ in range(4096):
        p = [rng.getrandbits(32) for _ in range(5)]
        q, _ = learn([value(p, x, 1 << 32) for x in range(5)])
        inputs = [0,1,2,3,4,0x7fffffff,0x80000000,0xffffffff]
        inputs += [rng.getrandbits(32) for _ in range(32)]
        for x in inputs:
            assert value(p,x,1 << 32) == value(q,x,1 << 32)
            random_comparisons += 1
    sources = [Path(__file__).with_name(n) for n in
               ['audit.py','probe.py','wasm_gate.py','blackbox.py','README.md']]
    root = Path(__file__).resolve().parents[2]
    sources += [root/'research/observation-synthesis'/n for n in ['transform.py','core.py']]
    hashes = []
    for p in sources:
        rel = p.relative_to(root)
        out = destination/'source'/rel
        out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,out)
        hashes.append({'path':rel.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    artifacts = []
    for p in sorted(wasm_root.rglob('*')):
        if p.is_file():
            artifacts.append({'path':p.relative_to(wasm_root).as_posix(),
                              'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    result = {'source_matches_recorded_run':source_matches,
              'wasm_manifest_hashes_checked':len(manifest['rows']),
              'all_mod8_quartics':cases,'all_mod8_value_comparisons':comparisons,
              'random_mod32_quartics':4096,'random_mod32_value_comparisons':random_comparisons,
              'mismatches':0,'sources':hashes,'artifacts':artifacts,
              'scope':'Implementation tests under the known integer-polynomial degree <= 4 promise; not a degree inference algorithm.'}
    (destination/'audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['sources','artifacts']}))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('wasm_run',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    run(args.wasm_run,args.output)
