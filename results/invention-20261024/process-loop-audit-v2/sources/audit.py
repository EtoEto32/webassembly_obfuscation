"""Independent-engine replay and artifact integrity for the feasibility screen."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import check as m


def main():
    p = argparse.ArgumentParser()
    p.add_argument('main', type=Path)
    p.add_argument('followup', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    pinned = 0
    for folder in (args.main, args.followup):
        hashes = json.loads((folder/'sha256.json').read_text(encoding='utf-8'))
        for name, wanted in hashes.items():
            actual = hashlib.sha256((folder/name).read_bytes()).hexdigest()
            if actual != wanted:
                raise ValueError('artifact changed: '+str(folder/name))
            pinned += 1
    cases = json.loads((args.followup/'cases.json').read_text(encoding='utf-8'))
    checks = [cases['solver_cases'][i] for i in (0, 259, 514)]
    engine = []
    for file in cases['solver_files']:
        mod = m.w.parse(m.w.tool('wasm2wat', [args.followup/file, '--fold-exprs', '--no-debug-names']))
        export = [n for n in mod[1:] if n[0] == 'export' and n[1] == '"solve"']
        assert len(export) == 1 and export[0][2][0] == 'func'
        target = export[0][2][1]
        for i, c in enumerate(checks):
            consts = [['i32.const', str(x if x < 2**31 else x-2**32)] for x in c['input']]
            mod.append(['func', ['export', '"case'+str(i)+'"'], ['result', 'i32', 'i32', 'i32'],
                        ['call', target, *consts]])
        src = out/(Path(file).stem+'-wrappers.wat')
        src.write_text(m.w.emit(mod), encoding='utf-8')
        dst = src.with_suffix('.wasm')
        m.w.tool('wat2wasm', [src, '-o', dst])
        m.w.tool('wasm-validate', [dst])
        stdout = m.w.tool('wasm-interp', [dst, '--run-all-exports'])
        (out/(dst.stem+'.txt')).write_text(stdout, encoding='utf-8')
        lines = [line for line in stdout.splitlines() if line.startswith('case')]
        assert len(lines) == len(checks)
        for i, line in enumerate(lines):
            assert line.startswith('case'+str(i)+'() => ')
            actual = list(map(int, re.findall(r'i32:(\d+)', line)))
            assert actual == checks[i]['expected'], (line, checks[i])
            engine.append({'module': file, 'case': i, 'values': actual})
    here = Path(__file__).parent
    for file in here.glob('*.py'):
        ast.parse(file.read_text(encoding='utf-8'))
    for file in here.glob('*.cjs'):
        subprocess.run(['node', '--check', str(file)], check=True, capture_output=True, text=True)
    protected = {
        'paper/main.tex': 'db94c578a9d573b700756daeebaabfbcbfc3fa0c896ac1a47d491bc09cc12225',
        'paper/README.md': '10e8eee3c2f27f66a7f2df2d4807f4aca97bde8a49eb8f2a3be186e6d550f2d0'}
    for file, expected in protected.items():
        assert hashlib.sha256((m.ROOT/file).read_bytes()).hexdigest() == expected
    report = {'pins_verified': pinned, 'mismatches': [], 'wabt_calls': len(engine),
              'wabt_values': engine, 'protected_files_unchanged': protected,
              'scope': 'feasibility result verification, not goal completion'}
    (out/'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    snapshot = out/'sources'
    snapshot.mkdir()
    for name in ('audit.py', 'check.py'):
        shutil.copy2(here/name, snapshot/name)
    shutil.copy2(m.ROOT/'research/connectivity-elimination/prototype.py', snapshot/'wasm-helper.py')
    hashes = {str(f.relative_to(out)).replace('\\','/'): hashlib.sha256(f.read_bytes()).hexdigest()
              for f in sorted(out.rglob('*')) if f.is_file()}
    (out/'sha256.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
