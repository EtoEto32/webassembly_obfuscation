"""Build small, real Wasm probes. Not a Component Model implementation."""
import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('wasm_helper', ROOT / 'research/connectivity-elimination/prototype.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(mod):
    """Conservative syntactic write upper bound; unknown syntax => full copy.

    Only a single, memory-exporting, import-free callback is certified.
    Branches are joined by union, rather than predicting a branch from input.
    Expression operands are interpreted as i32; memarg offsets do NOT wrap.
    """
    def has_shared(x):
        return x == 'shared' if isinstance(x, str) else any(has_shared(y) for y in x)
    if has_shared(mod):
        return {'kind': 'reject', 'reason': 'shared memory is outside the coherent-snapshot contract'}
    allowed_top = {'type', 'func', 'memory', 'export'}
    if any(x[0] not in allowed_top for x in mod[1:]):
        return {'kind': 'full', 'reason': 'import or unsupported module item'}
    funcs = [x for x in mod[1:] if x[0] == 'func']
    mems = [x for x in mod[1:] if x[0] == 'memory']
    exports = {x[1]: x[2] for x in mod[1:] if x[0] == 'export'}
    if len(funcs) != 1 or len(mems) != 1 or 'shared' in mems[0] or exports.get('"callback"') != ['func', '0']:
        return {'kind': 'full', 'reason': 'unsupported functions/memory/entry'}
    writes = []

    def val(x):
        if x[0] == 'i32.const' and len(x) == 2:
            return ['const', int(x[1]) & 0xffffffff]
        if x[0] == 'local.get' and len(x) == 2 and 0 <= int(x[1]) < 3:
            return ['arg', int(x[1])]
        if x[0] in ('i32.add', 'i32.sub', 'i32.and') and len(x) == 3:
            return [x[0][4:], val(x[1]), val(x[2])]
        raise ValueError('unsupported address/value expression')

    def walk(x):
        if not isinstance(x, list):
            raise ValueError('unexpected atom')
        op = x[0]
        sizes = {'i32.store8': 1, 'i32.store16': 2, 'i32.store': 4}
        if op in sizes:
            args = [y for y in x[1:] if isinstance(y, list)]
            attrs = [y for y in x[1:] if isinstance(y, str)]
            if len(args) != 2 or any(not a.startswith(('offset=', 'align=')) for a in attrs):
                raise ValueError('unsupported store form')
            offset = next((int(a.split('=')[1]) for a in attrs if a.startswith('offset=')), 0)
            val(args[1])  # no hidden calls/writes in the value expression
            writes.append({'addr': val(args[0]), 'offset': offset, 'length': ['const', sizes[op]]})
        elif op in ('memory.fill', 'memory.copy'):
            if len(x) != 4 or not all(isinstance(y, list) for y in x[1:]):
                raise ValueError('unsupported bulk memory form')
            val(x[2])
            writes.append({'addr': val(x[1]), 'offset': 0, 'length': val(x[3])})
        elif op == 'if':
            val(x[1])
            for y in x[2:]:
                walk(y)
        elif op in ('then', 'else', 'block'):
            for y in x[1:]:
                walk(y)
        elif op == 'nop':
            if len(x) != 1:
                raise ValueError('malformed nop')
        else:
            raise ValueError('unsupported instruction: ' + str(op))
    try:
        f = funcs[0]
        if any(isinstance(x, list) and x[0] in ('local', 'result') for x in f[1:]):
            raise ValueError('locals/results unsupported')
        params = [t for x in f[1:] if isinstance(x, list) and x[0] == 'param' for t in x[1:]]
        if params != ['i32'] * 3:
            raise ValueError('unexpected signature')
        for x in f[1:]:
            if isinstance(x, str):
                raise ValueError('unexpected function name')
            if x[0] not in ('type', 'param'):
                walk(x)
        return {'kind': 'ranges', 'writes': writes}
    except (ValueError, IndexError) as e:
        return {'kind': 'full', 'reason': str(e)}


def build(out):
    out.mkdir(parents=True, exist_ok=False)
    (out / 'sources').mkdir()
    for name in ('probe.py', 'probe.cjs', 'plan.md'):
        shutil.copy2(Path(__file__).with_name(name), out / 'sources' / name)
    shutil.copy2(ROOT / 'research/connectivity-elimination/prototype.py', out / 'sources/wasm-helper.py')
    a = '''(module
      (import "host" "prepare" (func $prepare (param i32 i32 i32) (result i32)))
      (func (export "request") (param i32 i32 i32) (result i32)
        (call $prepare (local.get 0) (local.get 1) (local.get 2))))'''
    c = '''(module
      (import "host" "event" (func $event (param i32 i32) (result i32)))
      (func (export "event") (param i32 i32) (result i32)
        (call $event (local.get 0) (local.get 1))))'''
    bodies = {
        'byte': '(i32.store8 (local.get 0) (local.get 1))',
        'word-offset': '(i32.store offset=7 (local.get 0) (local.get 1))',
        'wrapped-address': '(i32.store16 (i32.add (local.get 0) (i32.const 7)) (local.get 1))',
        'two-writes': '(i32.store (local.get 0) (local.get 1)) (i32.store (i32.add (local.get 0) (i32.const 12)) (local.get 1))',
        'fill': '(memory.fill (local.get 0) (local.get 1) (local.get 2))',
        'copy': '(memory.copy (local.get 0) (i32.const 1024) (local.get 2))',
        'branch': '(if (local.get 2) (then (i32.store (local.get 0) (local.get 1))) (else (i32.store (i32.const 4094) (local.get 1))))',
        'partial-trap': '(i32.store8 (i32.const 4) (local.get 1)) (i32.store (i32.const 131071) (local.get 1))',
        'unknown-load': '(i32.store (i32.load (i32.const 16)) (local.get 1))',
    }
    modules = {'authority': a, 'budget': c}
    for name, body in bodies.items():
        modules['snapshot-' + name] = '(module (memory (export "memory") 2 4) (func (export "callback") (param i32 i32 i32) ' + body + '))'
    manifest = []
    timings = []
    for name, wat in modules.items():
        src = out / (name + '.wat')
        src.write_text(wat, encoding='utf8')
        raw = out / (name + '-raw.wasm')
        start = time.perf_counter()
        w.tool('wat2wasm', [src, '-o', raw])
        timings.append({'name': name, 'stage': 'assemble', 'ms': (time.perf_counter()-start)*1000})
        opt = out / (name + '-O3.wasm')
        start = time.perf_counter()
        w.tool('wasm-opt', [raw, '-O3', '--enable-bulk-memory', '-o', opt])
        timings.append({'name': name, 'stage': 'O3', 'ms': (time.perf_counter()-start)*1000})
        for path in (raw, opt):
            w.tool('wasm-validate', [path])
            entry = {'name': name, 'file': path.name, 'sha256': digest(path), 'bytes': path.stat().st_size}
            if name.startswith('snapshot-'):
                text = w.tool('wasm2wat', [path, '--fold-exprs'])
                path.with_suffix('.wat').write_text(text, encoding='utf8')
                start = time.perf_counter()
                entry['summary'] = summarize(w.parse(text))
                entry['summary_ms'] = (time.perf_counter()-start)*1000
            manifest.append(entry)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    r = subprocess.run(['node', str(Path(__file__).with_suffix('.cjs')), str(out)], capture_output=True, text=True, timeout=120)
    (out / 'node-stdout.txt').write_text(r.stdout, encoding='utf8')
    (out / 'node-stderr.txt').write_text(r.stderr, encoding='utf8')
    (out / 'build.json').write_text(json.dumps({'platform': platform.platform(), 'python': platform.python_version(), 'wabt': w.tool('wat2wasm', ['--version']).strip(), 'binaryen': w.tool('wasm-opt', ['--version']).strip(), 'timings': timings, 'node_exit': r.returncode}, indent=2), encoding='utf8')
    files = {str(p.relative_to(out)): digest(p) for p in out.rglob('*') if p.is_file()}
    (out / 'sha256.json').write_text(json.dumps(files, indent=2), encoding='utf8')
    if r.returncode:
        raise RuntimeError(r.stderr)
    print(r.stdout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    build(parser.parse_args().output.resolve())
