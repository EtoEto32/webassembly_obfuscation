"""Exact-template Wasm -> known group-point matcher. NOT a novel cryptosystem."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research/observation-synthesis'))
spec = importlib.util.spec_from_file_location('point_wat', ROOT / 'research/observation-synthesis/transform.py')
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)
TOOLS = Path(os.environ.get('WASM_TOOLS_ROOT', ROOT / '.tools'))
P = int('''FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1
29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD
EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245
E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED
EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE45B3D
C2007CB8 A163BF05 98DA4836 1C55D39A 69163FA8 FD24CF5F
83655D23 DCA3AD96 1C62F356 208552BB 9ED52907 7096966D
670C354E 4ABC9804 F1746C08 CA18217C 32905E46 2E36CE3B
E39E772C 180E8603 9B2783A2 EC07A28F B5C55DF0 6F4C52C9
DE2BCBF6 95581718 3995497C EA956AE5 15D22618 98FA0510
15728E5A 8AACAA68 FFFFFFFF FFFFFFFF'''.replace(' ', '').replace('\n', ''), 16)
Q = (P - 1) // 2
R = 1 << 2048
ONE = R % P
G = 2


def tool(name, args):
    folder = 'binaryen-version_133' if name == 'wasm-opt' else 'wabt-1.0.42'
    return subprocess.run([str(TOOLS / folder / 'bin' / (name + '.exe')), *map(str, args)],
                          check=True, capture_output=True, text=True, timeout=120).stdout


def assemble(wat, out):
    out = Path(out)
    if out.exists() or out.with_suffix('.wat').exists():
        raise ValueError('Refuse overwrite')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix('.wat').write_text(wat, encoding='utf-8')
    tool('wat2wasm', [out.with_suffix('.wat'), '-o', out])
    tool('wasm-validate', [out])


BOUNDS = '''
  (if (i64.gt_u (i64.add (i64.extend_i32_u (local.get $ptr))
                         (i64.extend_i32_u (local.get $len))) (i64.const 65536))
    (then (drop (i32.load (i32.const 65536)))))
'''


def source(pattern):
    if not 1 <= len(pattern) <= 255:
        raise ValueError('Pattern length must be 1..255')
    checks = '\n'.join(f'''(if (i32.ne (i32.load8_u offset={j} (local.get $ptr)) (i32.const {b}))
         (then (return (i32.const 0))))''' for j, b in enumerate(pattern))
    return f'''(module
      (memory (export "memory") 1 1)
      (func $check (param $ptr i32) (result i32) {checks} (i32.const 1))
      (func (export "run") (param $ptr i32) (param $len i32) (result i32)
        (local $i i32) (local $end i32)
        {BOUNDS}
        (if (i32.lt_u (local.get $len) (i32.const {len(pattern)})) (then (return (i32.const -1))))
        (local.set $end (i32.sub (local.get $len) (i32.const {len(pattern)})))
        (loop $scan
          (if (call $check (i32.add (local.get $ptr) (local.get $i))) (then (return (local.get $i))))
          (if (i32.eq (local.get $i) (local.get $end)) (then (return (i32.const -1))))
          (local.set $i (i32.add (local.get $i) (i32.const 1))) (br $scan))
        (unreachable)))'''


def inspect(src):
    tool('wasm-validate', [src])
    ast = W.parse(tool('wasm2wat', [src, '--fold-exprs']))
    fs = [x for x in ast[1:] if x[0] == 'func']
    if len(fs) != 2:
        raise ValueError('Only the exact fixed-pattern template is accepted')
    body = [x for x in fs[0][1:] if isinstance(x, list) and x[0] not in ('type', 'param', 'result')]
    try:
        if body[-1] != ['i32.const', '1']:
            raise ValueError('Bad check tail')
        pattern = bytes(int(x[1][2][1]) for x in body[:-1])
    except (IndexError, ValueError, TypeError) as e:
        raise ValueError('Not a literal pattern template') from e
    with tempfile.TemporaryDirectory(prefix='point-template-') as td:
        expected = Path(td) / 'expected.wasm'
        assemble(source(pattern), expected)
        if ast != W.parse(tool('wasm2wat', [expected, '--fold-exprs'])):
            raise ValueError('AST differs from the supported template')
    return pattern


def mont_code(t):
    # N'= -p^-1 mod 2^32 = 1, since p ends in FFFFFFFF.
    return f'''
    (func $ge (param $a i32) (param $b i32) (result i32) (local $j i32) (local $x i32) (local $y i32)
      (local.set $j (i32.const 256))
      (loop $cmp
        (local.set $j (i32.sub (local.get $j) (i32.const 4)))
        (local.set $x (i32.load $work (i32.add (local.get $a) (local.get $j))))
        (local.set $y (i32.load $work (i32.add (local.get $b) (local.get $j))))
        (if (i32.ne (local.get $x) (local.get $y))
          (then (return (i32.gt_u (local.get $x) (local.get $y)))))
        (br_if $cmp (local.get $j))) (i32.const 1))
    (func $mont (param $a i32) (param $b i32) (param $out i32)
      (local $i i32) (local $j i32) (local $k i32)
      (local $carry i64) (local $m i64) (local $z i64) (local $x i64) (local $y i64)
      (memory.fill $work (i32.const {t}) (i32.const 0) (i32.const 520))
      (loop $product_i
        (local.set $carry (i64.const 0)) (local.set $j (i32.const 0))
        (local.set $m (i64.load32_u $work (i32.add (local.get $b) (local.get $i))))
        (loop $product_j
          (local.set $k (i32.add (i32.const {t}) (i32.add (local.get $i) (local.get $j))))
          (local.set $z (i64.add (i64.add
            (i64.mul (local.get $m) (i64.load32_u $work (i32.add (local.get $a) (local.get $j))))
            (i64.load32_u $work (local.get $k))) (local.get $carry)))
          (i64.store32 $work (local.get $k) (local.get $z))
          (local.set $carry (i64.shr_u (local.get $z) (i64.const 32)))
          (local.set $j (i32.add (local.get $j) (i32.const 4)))
          (br_if $product_j (i32.lt_u (local.get $j) (i32.const 256))))
        (i64.store32 $work (i32.add (i32.const {t+256}) (local.get $i)) (local.get $carry))
        (local.set $i (i32.add (local.get $i) (i32.const 4)))
        (br_if $product_i (i32.lt_u (local.get $i) (i32.const 256))))
      (local.set $i (i32.const 0))
      (loop $reduce_i
        (local.set $m (i64.load32_u $work (i32.add (i32.const {t}) (local.get $i))))
        (local.set $carry (i64.const 0)) (local.set $j (i32.const 0))
        (loop $reduce_j
          (local.set $k (i32.add (i32.const {t}) (i32.add (local.get $i) (local.get $j))))
          (local.set $z (i64.add (i64.add (i64.load32_u $work (local.get $k))
             (i64.mul (local.get $m) (i64.load32_u $work (local.get $j)))) (local.get $carry)))
          (i64.store32 $work (local.get $k) (local.get $z))
          (local.set $carry (i64.shr_u (local.get $z) (i64.const 32)))
          (local.set $j (i32.add (local.get $j) (i32.const 4)))
          (br_if $reduce_j (i32.lt_u (local.get $j) (i32.const 256))))
        (local.set $k (i32.add (i32.const {t+256}) (local.get $i)))
        (loop $propagate
          (local.set $z (i64.add (i64.load32_u $work (local.get $k)) (local.get $carry)))
          (i64.store32 $work (local.get $k) (local.get $z))
          (local.set $carry (i64.shr_u (local.get $z) (i64.const 32)))
          (local.set $k (i32.add (local.get $k) (i32.const 4)))
          (br_if $propagate (i64.ne (local.get $carry) (i64.const 0))))
        (local.set $i (i32.add (local.get $i) (i32.const 4)))
        (br_if $reduce_i (i32.lt_u (local.get $i) (i32.const 256))))
      (if (i32.or (i32.load $work (i32.const {t+512})) (call $ge (i32.const {t+256}) (i32.const 0)))
        (then
          (local.set $j (i32.const 0)) (local.set $carry (i64.const 0))
          (loop $subtract
            (local.set $x (i64.load32_u $work (i32.add (i32.const {t+256}) (local.get $j))))
            (local.set $y (i64.add (i64.load32_u $work (local.get $j)) (local.get $carry)))
            (i64.store32 $work (i32.add (local.get $out) (local.get $j)) (i64.sub (local.get $x) (local.get $y)))
            (local.set $carry (i64.extend_i32_u (i64.lt_u (local.get $x) (local.get $y))))
            (local.set $j (i32.add (local.get $j) (i32.const 4)))
            (br_if $subtract (i32.lt_u (local.get $j) (i32.const 256)))))
        (else (memory.copy $work $work (local.get $out) (i32.const {t+256}) (i32.const 256)))))
    '''


def group_module(pattern, method, audit=False):
    length = len(pattern)
    if not 1 <= length <= 255 or 256 ** length >= Q:
        raise ValueError('Exact injective domain exceeded')
    rolling = method == 'rolling'
    a, d = 1024, 66560
    h = 132096 if rolling else 66560
    t = h + 256
    data = bytearray(h)
    def put(off, x): data[off:off+256] = x.to_bytes(256, 'little')
    put(0, P); put(256, ONE); put(512, pow(G, int.from_bytes(pattern, 'big'), P) * ONE % P)
    x = ONE
    for b in range(256): put(a+256*b, x); x = x * G % P
    if rolling:
        step = pow(G, -pow(256, length, Q) % Q, P)
        x = ONE
        for b in range(256): put(d+256*b, x); x = x * step % P
    data_token = '"' + ''.join('\\%02x' % b for b in data) + '"'
    advance = f'''(local.set $k (i32.const 8)) (loop $square
      (call $mont (i32.const {h}) (i32.const {h}) (i32.const {h}))
      (local.set $k (i32.sub (local.get $k) (i32.const 1))) (br_if $square (local.get $k)))'''
    incoming = f'''(call $mont (i32.const {h})
      (i32.add (i32.const {a}) (i32.shl (i32.load8_u (i32.add (local.get $ptr) (local.get $i))) (i32.const 8)))
      (i32.const {h}))'''
    if rolling:
        scan = f'''(memory.copy $work $work (i32.const {h}) (i32.const 256) (i32.const 256))
          (loop $scan {advance}
            (if (i32.ge_u (local.get $i) (i32.const {length})) (then
              (call $mont (i32.const {h})
                (i32.add (i32.const {d}) (i32.shl (i32.load8_u
                  (i32.add (local.get $ptr) (i32.sub (local.get $i) (i32.const {length})))) (i32.const 8)))
                (i32.const {h}))))
            {incoming}
            (if (i32.ge_u (local.get $i) (i32.const {length-1}))
              (then (if (call $equal) (then (return (i32.sub (local.get $i) (i32.const {length-1})))))))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br_if $scan (i32.lt_u (local.get $i) (local.get $len))))'''
    else:
        scan = f'''(loop $scan
          (memory.copy $work $work (i32.const {h}) (i32.const 256) (i32.const 256))
          (local.set $i (local.get $start))
          (loop $window {advance} {incoming}
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br_if $window (i32.lt_u (local.get $i) (i32.add (local.get $start) (i32.const {length})))))
          (if (call $equal) (then (return (local.get $start))))
          (local.set $start (i32.add (local.get $start) (i32.const 1)))
          (br_if $scan (i32.le_u (local.get $start) (i32.sub (local.get $len) (i32.const {length})))))'''
    audit_exports = '(export "work" (memory $work)) (export "mont" (func $mont))' if audit else ''
    return f'''(module
      (memory (export "memory") 1 1) (memory $work {math.ceil((t+520)/65536)} {math.ceil((t+520)/65536)})
      (data (memory $work) (i32.const 0) {data_token})
      {mont_code(t)}
      (func $equal (result i32) (local $j i32)
        (loop $eq
          (if (i64.ne (i64.load $work (i32.add (i32.const {h}) (local.get $j)))
                      (i64.load $work (i32.add (i32.const 512) (local.get $j)))) (then (return (i32.const 0))))
          (local.set $j (i32.add (local.get $j) (i32.const 8)))
          (br_if $eq (i32.lt_u (local.get $j) (i32.const 256)))) (i32.const 1))
      (func (export "run") (param $ptr i32) (param $len i32) (result i32)
        (local $i i32) (local $start i32) (local $k i32)
        {BOUNDS}
        (if (i32.lt_u (local.get $len) (i32.const {length})) (then (return (i32.const -1))))
        {scan} (i32.const -1)) {audit_exports})''', {'h': h, 'scratch': t, 'private_pages': math.ceil((t+520)/65536)}


def transform(src, out, method='rolling'):
    start = time.perf_counter_ns()
    pattern = inspect(src)
    wat, layout = group_module(pattern, method)
    assemble(wat, out)
    return {'method': method, 'length': len(pattern), **layout,
            'transformation_ns': time.perf_counter_ns()-start,
            'input_sha256': hashlib.sha256(Path(src).read_bytes()).hexdigest(),
            'output_sha256': hashlib.sha256(Path(out).read_bytes()).hexdigest(),
            'output_bytes': Path(out).stat().st_size,
            'novelty': 'known point-function principle; rolling composition not established as novel'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('input', type=Path); ap.add_argument('output', type=Path)
    ap.add_argument('--method', choices=['rolling', 'recompute'], default='rolling')
    args = ap.parse_args()
    result = transform(args.input, args.output, args.method)
    Path(str(args.output)+'.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))
