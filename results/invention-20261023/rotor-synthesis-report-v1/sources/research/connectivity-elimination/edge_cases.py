"""Supported degenerate graphs and explicit unsupported-input rejection."""
import argparse
import json
from pathlib import Path
import subprocess
import prototype as p

ap = argparse.ArgumentParser()
ap.add_argument('directory', type=Path)
a = ap.parse_args()
dest = a.directory / 'edge-cases'
dest.mkdir(exist_ok=False)
cases = [('zero', ('const', 0)), ('one', ('const', p.MASK)), ('input', ('var', 0)),
         ('negated', ('xor', ('var', 0), ('const', p.MASK)))]
values = [0, 1, 2, 0x7fffffff, 0x80000000, p.MASK, 0xaaaaaaaa, 0x55555555]
jobs = []
for name, tree in cases:
    src = dest / (name + '.wasm')
    wp = src.with_suffix('.wat')
    wp.write_text(p.plain_wat(1, '"run"', tree), encoding='utf-8')
    p.tool('wat2wasm', [wp, '-o', src])
    for fraction in (0, 0.5, 0.8):
        out = dest / f'{name}-{fraction}.wasm'
        p.transform(src, out, fraction)
        expected = [(0 if name == 'zero' else p.MASK if name == 'one' else x if name == 'input' else x ^ p.MASK) for x in values]
        jobs.append({'file': str(out.resolve()), 'values': values, 'expected': expected})
rejects = {
    'memory': '(module (memory 1) (func (export "run") (param i32) (result i32) (local.get 0)))',
    'trapping_division': '(module (func (export "run") (param i32) (result i32) (i32.div_u (i32.const 1) (local.get 0))))',
    'non_mask_constant': '(module (func (export "run") (param i32) (result i32) (i32.const 1)))',
    'call': '(module (func (result i32) (i32.const 0)) (func (export "run") (param i32) (result i32) (call 0)))',
    'float': '(module (func (export "run") (param f32) (result f32) (local.get 0)))',
}
rejection_rows = []
for name, text in rejects.items():
    wp = dest / ('reject-' + name + '.wat')
    wp.write_text(text, encoding='utf-8')
    src = wp.with_suffix('.wasm')
    p.tool('wat2wasm', [wp, '-o', src])
    out = dest / ('unexpected-' + name + '.wasm')
    try:
        p.transform(src, out, 0.5)
    except ValueError as exc:
        assert not out.exists()
        rejection_rows.append({'case': name, 'status': 'rejected', 'reason': str(exc)})
    else:
        raise AssertionError('Unsupported input accepted: ' + name)
jobs_path = dest / 'jobs.json'
jobs_path.write_text(json.dumps(jobs), encoding='utf-8')
runner = dest / 'run.cjs'
runner.write_text('''const fs=require('fs');
(async()=>{let count=0; for(const j of JSON.parse(fs.readFileSync(process.argv[2]))){
const e=(await WebAssembly.instantiate(fs.readFileSync(j.file))).instance.exports;
for(let i=0;i<j.values.length;i++){if((e.run(j.values[i])>>>0)!==j.expected[i])throw Error(j.file);count++;}}
console.log(JSON.stringify({calls:count,mismatches:0}));})().catch(e=>{console.error(e);process.exitCode=1;});
''', encoding='utf-8')
run = subprocess.run(['node', str(runner), str(jobs_path)], capture_output=True, text=True, check=True, timeout=30)
result = {'accepted_conditions': len(jobs), 'execution': json.loads(run.stdout), 'rejections': rejection_rows}
(a.directory / 'edge-cases.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result['execution']))
