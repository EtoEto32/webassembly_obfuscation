"""Bounded prototype; originality remains unresolved. Standard library only."""
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ZERO = (0, 0, 0, 0)
def const(n):
    return {ZERO: n}
def var(i):
    e = list(ZERO)
    e[i] = 1
    return {tuple(e): 1}
def add(a, b, sign=1):
    c = a.copy()
    for e, v in b.items():
        c[e] = c.get(e, 0) + sign*v
    return {e: v for e, v in c.items() if v}
def mul(a, b):
    c = {}
    for e, u in a.items():
        for f, v in b.items():
            k = tuple(x+y for x, y in zip(e, f))
            c[k] = c.get(k, 0) + u*v
    return {e: v for e, v in c.items() if v}
def wat(p):
    terms = []
    for e, c in sorted(p.items()):
        term = f'(i32.const {c})'
        for name, degree in zip(('x', 'y', 'z', 't'), e):
            for _ in range(degree):
                term = f'(i32.mul {term} (local.get ${name}))'
        terms.append(term)
    out = '(i32.const 0)'
    for term in terms:
        out = f'(i32.add {out} {term})'
    return out

x, y, z, t = [var(i) for i in range(4)]
a, b = add(z, add(x, y), -1), add(t, mul(x, y), -1)
q1 = add(a, mul(mul(a, add(a, const(1))), b))
q2 = add(b, mul(mul(b, add(b, const(1))), a))
source = f'''(module
 (func (export "before") (param $x i32) (param $y i32) (result i32 i32)
   (i32.add (local.get $x) (local.get $y))
   (i32.mul (local.get $x) (local.get $y)))
 (func $after_seed (export "after_seed") (param $x i32) (param $y i32)
   (param $z i32) (param $t i32) (result i32 i32)
   (local $nz i32) (local $nt i32) (local $i i32)
   (loop $again
     (local.set $nz (i32.sub (local.get $z) {wat(q1)}))
     (local.set $nt (i32.sub (local.get $t) {wat(q2)}))
     (local.set $z (local.get $nz))
     (local.set $t (local.get $nt))
     (local.set $i (i32.add (local.get $i) (i32.const 1)))
     (br_if $again (i32.lt_u (local.get $i) (i32.const 6))))
   (local.get $z) (local.get $t))
 (func (export "after") (param $x i32) (param $y i32) (result i32 i32)
   (call $after_seed (local.get $x) (local.get $y) (i32.const 0) (i32.const 0))))
'''
(HERE/'example.wat').write_text(source, encoding='utf-8')
subprocess.run([str(ROOT/'.tools/wabt-1.0.42/bin/wat2wasm.exe'),
                str(HERE/'example.wat'), '-o', str(HERE/'example.wasm')], check=True)
result = subprocess.run(['C:/Program Files/nodejs/node.exe', str(HERE/'verify.cjs')],
                        check=True, capture_output=True, text=True)
(HERE/'results.json').write_text(result.stdout, encoding='utf-8')
print(result.stdout)
