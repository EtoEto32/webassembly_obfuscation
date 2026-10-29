"""Mutable fixed-key fixtures; a falsification gate, not a new obfuscator."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / 'research/polynomial-lookup'))
spec = importlib.util.spec_from_file_location('static_poly', ROOT / 'research/polynomial-lookup/prototype.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
P = base.P
q = base.q


def canonical(items):
    result = {}
    for k, v in items:
        if not 0 <= k < 2**32 or not 0 <= v < 2**32:
            raise ValueError('u32 required')
        result.setdefault(k, v)
    if len(result) > 512:
        raise ValueError('512-key limit')
    return sorted(result.items())


def array_text(items):
    items = canonical(items)
    return base.array_text(items)[:-1] + f'''
      (func (export "set") (param $k i32) (param $v i32) (result i32) (local $p i32)
       (local.set $p (i32.const 64))
       (block $done (loop $scan
        (br_if $done (i32.ge_u (local.get $p) (i32.const {64+8*len(items)})))
        (if (i32.eq (i32.load (local.get $p)) (local.get $k)) (then
          (i32.store offset=4 (local.get $p) (local.get $v)) (return (i32.const 1))))
        (local.set $p (i32.add (local.get $p) (i32.const 8))) (br $scan))) (i32.const 0)))'''


def poly_text(items):
    items = canonical(items)
    n = sum(k < P for k, _ in items)
    lo, hi, scratch = 28+4*(n+1), 28+4*(2*n+1), 28+4*(3*n+1)
    update = []
    for ptr, alpha in ((lo, '$a0'), (hi, '$a1')):
        update.append(f'''(i64.store32 (i32.add (i32.const {ptr}) (local.get $off))
          (i64.rem_u (i64.add
            (i64.load32_u (i32.add (i32.const {ptr}) (local.get $off)))
            (i64.mul (local.get {alpha}) (local.get $b))) (i64.const {P})))''')
    return base.poly_text(items)[:-1] + f'''
     (func $inv (param $a i64) (result i64) (local $r i64) (local $e i32)
       (local.set $r (i64.const 1)) (local.set $e (i32.const {P-2}))
       (loop $pow
        (if (i32.and (local.get $e) (i32.const 1)) (then
          (local.set $r (i64.rem_u (i64.mul (local.get $r) (local.get $a)) (i64.const {P})))))
        (local.set $e (i32.shr_u (local.get $e) (i32.const 1)))
        (local.set $a (i64.rem_u (i64.mul (local.get $a) (local.get $a)) (i64.const {P})))
        (br_if $pow (local.get $e))) (local.get $r))
     (func (export "set") (param $key i32) (param $value i32) (result i32)
       (local $x i64) (local $v i64) (local $b i64) (local $den i64)
       (local $a0 i64) (local $a1 i64) (local $j i32) (local $off i32)
       (local.set $x (i64.extend_i32_u (local.get $key)))
       (if (i64.ge_u (local.get $x) (i64.const {P})) (then
        (local.set $j (i32.sub (local.get $key) (i32.const {P})))
        (if (i32.and (i32.load (i32.const 4)) (i32.shl (i32.const 1) (local.get $j))) (then
          (i32.store (i32.add (i32.const 8) (i32.shl (local.get $j) (i32.const 2))) (local.get $value))
          (return (i32.const 1)))) (return (i32.const 0))))
       (if (i64.ne (call $eval (i32.const 28) (i32.const {n+1}) (local.get $x)) (i64.const 0))
         (then (return (i32.const 0))))
       ;; Synthetic division Q=P/(X-key); no persistent clear-key cache.
       (local.set $j (i32.const {n-1})) (local.set $b (i64.const 1))
       (i64.store32 (i32.const {scratch+4*(n-1)}) (local.get $b))
       (block $div_done (loop $div
         (br_if $div_done (i32.eqz (local.get $j)))
         (local.set $b (i64.rem_u (i64.add
            (i64.load32_u (i32.add (i32.const 28) (i32.shl (local.get $j) (i32.const 2))))
            (i64.mul (local.get $x) (local.get $b))) (i64.const {P})))
         (local.set $j (i32.sub (local.get $j) (i32.const 1)))
         (i64.store32 (i32.add (i32.const {scratch}) (i32.shl (local.get $j) (i32.const 2))) (local.get $b))
         (br $div)))
       (local.set $den (call $inv (call $eval (i32.const {scratch}) (i32.const {n}) (local.get $x))))
       (local.set $v (i64.extend_i32_u (local.get $value)))
       (local.set $a0 (i64.rem_u (i64.mul (local.get $den)
         (i64.rem_u (i64.sub (i64.add (i64.rem_u (local.get $v) (i64.const {P})) (i64.const {P}))
           (call $eval (i32.const {lo}) (i32.const {n}) (local.get $x))) (i64.const {P}))) (i64.const {P})))
       (local.set $a1 (i64.rem_u (i64.mul (local.get $den)
         (i64.rem_u (i64.sub (i64.add (i64.div_u (local.get $v) (i64.const {P})) (i64.const {P}))
           (call $eval (i32.const {hi}) (i32.const {n}) (local.get $x))) (i64.const {P}))) (i64.const {P})))
       (local.set $j (i32.const 0))
       (block $done (loop $apply
         (br_if $done (i32.ge_u (local.get $j) (i32.const {n})))
         (local.set $off (i32.shl (local.get $j) (i32.const 2)))
         (local.set $b (i64.load32_u (i32.add (i32.const {scratch}) (local.get $off))))
         {' '.join(update)}
         (i32.store (i32.add (i32.const {scratch}) (local.get $off)) (i32.const 0))
         (local.set $j (i32.add (local.get $j) (i32.const 1))) (br $apply)))
       (i32.const 1)))'''


def instrument(src, dst):
    module = q.read(src)
    if any(e[0] == 'export' and e[2][0] == 'memory' for e in module[1:]):
        raise ValueError('private memory required')
    module.append(['export', '"audit_memory"', ['memory', '0']])
    q.compile(q.w.emit(module), dst)
