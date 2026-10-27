"""Verify saved artifacts and compare an independent replay's binary outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import prototype as p

ap = argparse.ArgumentParser()
ap.add_argument('original', type=Path)
ap.add_argument('replay', type=Path)
ap.add_argument('output', type=Path)
a = ap.parse_args()
verified = {}
for directory in (a.original, a.replay):
    inventory = json.loads((directory / 'inventory.json').read_text())
    for row in inventory['files']:
        data = (directory / row['path']).read_bytes()
        assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
    verified[str(directory)] = len(inventory['files'])
first = json.loads((a.original / 'build.json').read_text())['conditions']
second = json.loads((a.replay / 'build.json').read_text())['conditions']
assert {x['file'] for x in first} == {x['file'] for x in second}
for row in first:
    assert (a.original / row['file']).read_bytes() == (a.replay / row['file']).read_bytes()
    assert (a.original / 'recovered-v2' / row['file']).read_bytes() == (a.replay / 'recovered-v2' / row['file']).read_bytes()
assert (a.original / 'inputs.json').read_bytes() == (a.replay / 'inputs.json').read_bytes()
for directory in (a.original, a.replay):
    summary = json.loads((directory / 'summary.json').read_text())
    assert summary['conditions'] == summary['recovered'] == 75
    assert summary['correctness_mismatches'] == summary['interpreter_mismatches'] == 0
tools = {}
for name, folder in [('wat2wasm', p.WABT), ('wasm2wat', p.WABT), ('wasm-validate', p.WABT), ('wasm-interp', p.WABT), ('wasm-opt', p.BINARYEN)]:
    exe = folder / (name + '.exe')
    tools[name] = {'path': str(exe), 'sha256_at_audit': hashlib.sha256(exe.read_bytes()).hexdigest(),
                   'version_at_audit': p.tool(name, ['--version']).strip()}
report = {'verified_inventories': verified, 'identical_input_binaries': len(first),
          'identical_recovered_binaries': len(first), 'identical_inputs': True, 'tools': tools,
          'note': 'Replay repeats the same cases; not additional independent input coverage. Hash audit does not establish novelty or general correctness.'}
with a.output.open('x', encoding='utf-8') as f:
    json.dump(report, f, indent=2)
print(json.dumps({k: v for k, v in report.items() if k != 'tools'}))
