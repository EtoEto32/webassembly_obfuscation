"""Binary-only, read-only memory32 load observation for evaluation.

Not an obfuscator or a NotDec implementation. The observer must return its
address/value arguments unchanged for the semantics-preservation claim.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(os.environ.get('WASM_TOOLS_ROOT', ROOT / '.tools'))
WABT = TOOLS / 'wabt-1.0.42/bin'
LOADS = {'i32.load': 4, 'i32.load8_s': 1, 'i32.load8_u': 1,
         'i32.load16_s': 2, 'i32.load16_u': 2}


def tool(name, args):
    return subprocess.run([str(WABT / (name + '.exe')), *map(str, args)],
                          check=True, capture_output=True, text=True, timeout=30).stdout


def parse(s):
    # Input is canonical WABT text, not arbitrary source WAT.
    ts = [t for t in re.findall(r'"(?:\\.|[^"\\])*"|;;[^\n]*|\(;[\s\S]*?;\)|[()]|[^\s()]+', s)
          if not t.startswith(';;') and not t.startswith('(;')]
    pos = 0

    def one():
        nonlocal pos
        t = ts[pos]
        pos += 1
        if t != '(':
            return t
        a = []
        while ts[pos] != ')':
            a.append(one())
        pos += 1
        return a

    a = one()
    if pos != len(ts) or a[0] != 'module':
        raise ValueError('Expected one canonical WABT module')
    return a


def emit(a):
    return '(' + ' '.join(map(emit, a)) + ')' if isinstance(a, list) else a


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def transform(src, out):
    if out.exists() or out.with_suffix('.trace.json').exists():
        raise ValueError('Refuse overwrite')
    t0 = time.perf_counter()
    tool('wasm-validate', [src])
    m = parse(tool('wasm2wat', [src, '--fold-exprs', '--generate-names', '--no-debug-names']))
    memories = [x for x in m[1:] if x[0] == 'memory']
    if len(memories) != 1 or any(x in ('shared', 'i64') for x in memories[0]):
        raise ValueError('Requires one non-shared defined memory32')
    if any(x[0] == 'import' for x in m[1:]):
        raise ValueError('Imported state/callbacks outside this evaluation profile')
    # Conservative rejection: all memory effects outside the fixture profile
    # are rejected, rather than silently yielding an incomplete trace.
    text = emit(m)
    if re.search(r'\b(?:i64|f32|f64|v128)\.load|\b(?:memory\.(?:copy|fill|init|grow)|\w+\.store|\w+\.atomic)', text):
        raise ValueError('Only read-only scalar i32 memory operations supported')
    sites, helpers = [], []
    prefix = '$__memory_audit_'
    if prefix in text:
        raise ValueError('Reserved instrumentation name collision')

    def walk(a):
        if not isinstance(a, list):
            return a
        if a and a[0] in LOADS:
            args = [v for v in a[1:] if isinstance(v, list)]
            attrs = [v for v in a[1:] if isinstance(v, str)]
            if len(args) != 1 or any(not v.startswith(('offset=', 'align=')) for v in attrs):
                raise ValueError('Unsupported load addressing profile')
            offset = next((int(v.split('=')[1]) for v in attrs if v.startswith('offset=')), 0)
            # The host records base + offset without i32 wrapping.
            if not 0 <= offset <= 0xffffffff:
                raise ValueError('Unsupported offset')
            site = len(sites)
            sites.append({'site': site, 'opcode': a[0], 'offset': offset, 'width': LOADS[a[0]]})
            operand = walk(args[0])
            name = prefix + str(site)
            attrs_text = ' '.join(attrs)
            signed_offset = offset if offset < 0x80000000 else offset - 0x100000000
            helpers.append(parse('(module (func ' + name + ' (param $a i32) (result i32) (local $v i32) '
                f'(local.set $v ({a[0]} {attrs_text} '
                f'(call {prefix}before (i32.const {site}) (local.get $a) (i32.const {signed_offset})))) '
                f'(call {prefix}after (i32.const {site}) (local.get $a) '
                f'(i32.const {signed_offset}) (local.get $v))))')[1])
            return ['call', name, operand]
        return [walk(v) for v in a]

    original = [walk(x) if x[0] == 'func' else x for x in m[1:]]
    imports = parse(f'''(module
      (import "audit" "before" (func {prefix}before (param i32 i32 i32) (result i32)))
      (import "audit" "after" (func {prefix}after (param i32 i32 i32 i32) (result i32))))''')[1:]
    # All old function references are named by WABT, so adding function imports
    # cannot redirect old call/export/start/element indices.
    result = ['module', *[x for x in original if x[0] == 'type'], *imports,
              *[x for x in original if x[0] != 'type'], *helpers]
    out.parent.mkdir(parents=True, exist_ok=True)
    wp = out.with_suffix('.wat')
    if wp.exists():
        raise ValueError('Refuse WAT overwrite')
    wp.write_text(emit(result) + '\n', encoding='utf-8')
    tool('wat2wasm', [wp, '-o', out])
    tool('wasm-validate', [out])
    report = {'input': str(src), 'output': str(out), 'input_sha256': sha(src),
              'output_sha256': sha(out), 'instrumenter_sha256': sha(__file__),
              'sites': sites, 'elapsed_seconds': time.perf_counter() - t0,
              'profile': 'single defined non-shared memory32; no original imports; read-only i32 loads',
              'semantics_condition': 'Both observer callbacks return their argument unchanged and have no program-visible effects.'}
    out.with_suffix('.trace.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('input', type=Path)
    ap.add_argument('output', type=Path)
    a = ap.parse_args()
    r = transform(a.input, a.output)
    print(json.dumps({'sites': len(r['sites']), 'output': str(a.output)}))
