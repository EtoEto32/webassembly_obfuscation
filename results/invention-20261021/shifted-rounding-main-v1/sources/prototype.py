"""Exact scaled binary32 grids in binary64; experimental, no security claim."""
import argparse
import importlib.util
import json
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('zero_sign_base', ROOT/'research/zero-sign-transport/prototype.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
q = base.q


def pow2(p):
    return f'(f64.const 0x1p{p:+d})'


def scale(expr, p):
    return f'(f64.mul {expr} {pow2(p)})' if p else expr


def quantizer():
    # Positive power-of-two scaling preserves zero sign. Exponents in [-32,32].
    return '''(func $quant (param $v f64) (param $p i32) (result f64)
      (local $raw i64) (local $a i64) (local $s i64) (local $e i32)
      (local $r i64) (local $m i64) (local $rounded i64)
      (local.set $raw (i64.reinterpret_f64 (local.get $v)))
      (local.set $a (i64.and (local.get $raw) (i64.const 9223372036854775807)))
      (local.set $s (i64.and (local.get $raw) (i64.const 9223372036854775808)))
      (local.set $e (i32.wrap_i64 (i64.shr_u (local.get $a) (i64.const 52))))
      (if (i32.or (i64.eqz (local.get $a)) (i32.eq (local.get $e) (i32.const 2047)))
        (then (return (local.get $v))))
      (local.set $e (i32.sub (i32.sub (local.get $e) (i32.const 1023)) (local.get $p)))
      (if (i32.gt_s (local.get $e) (i32.const 127))
        (then (return (f64.copysign (f64.const inf) (local.get $v)))))
      (if (i32.ge_s (local.get $e) (i32.const -126)) (then
        (local.set $rounded (i64.and
          (i64.add (i64.add (local.get $a) (i64.const 268435455))
            (i64.and (i64.shr_u (local.get $a) (i64.const 29)) (i64.const 1)))
          (i64.const 9223372036317904896)))
        (if (i64.ge_u (local.get $rounded)
          (i64.shl (i64.extend_i32_u (i32.add (local.get $p) (i32.const 1151))) (i64.const 52)))
          (then (return (f64.copysign (f64.const inf) (local.get $v)))))
        (return (f64.reinterpret_i64 (i64.or (local.get $s) (local.get $rounded))))))
      (if (i32.lt_s (local.get $e) (i32.const -150))
        (then (return (f64.copysign (f64.const 0) (local.get $v)))))
      (local.set $r (i64.extend_i32_u (i32.sub (i32.const -97) (local.get $e))))
      (local.set $m (i64.or (i64.and (local.get $a) (i64.const 4503599627370495))
                           (i64.const 4503599627370496)))
      (local.set $rounded (i64.shr_u
        (i64.add (i64.add (local.get $m)
          (i64.sub (i64.shl (i64.const 1) (i64.sub (local.get $r) (i64.const 1))) (i64.const 1)))
          (i64.and (i64.shr_u (local.get $m) (local.get $r)) (i64.const 1))) (local.get $r)))
      (f64.copysign (f64.mul (f64.convert_i64_u (local.get $rounded))
        (f64.reinterpret_i64 (i64.shl
          (i64.extend_i32_u (i32.add (local.get $p) (i32.const 874))) (i64.const 52))))
        (local.get $v)))'''


def generate(n, nodes, root, mode='shifted', seed=37):
    if mode == 'plain':
        return base.generate(n, nodes, root, 'plain', 0)[0], dict(mode=mode, scales=[0]*len(nodes))
    if mode not in ('eager', 'grid0', 'shifted'):
        raise ValueError(mode)
    rng = random.Random(seed)
    phases = [rng.choice([j for j in range(-32, 33) if j]) for _ in nodes] if mode != 'grid0' else [0]*len(nodes)
    v = lambda i: f'(local.get {n+i})'
    code = []
    for i, t in enumerate(nodes):
        if t[0] == 'input':
            expr = scale(f'(f64.promote_f32 (local.get {t[1]}))', phases[i])
        else:
            op, a, b = t
            if mode == 'eager':
                left = f'(f32.demote_f64 {scale(v(a), -phases[a])})'
                right = f'(f32.demote_f64 {scale(v(b), -phases[b])})'
                expr = scale(f'(f64.promote_f32 (f32.{op} {left} {right}))', phases[i])
            else:
                if op == 'mul':
                    expr = scale(f'(f64.mul {v(a)} {v(b)})', phases[i]-phases[a]-phases[b])
                else:
                    expr = f'(f64.{op} {scale(v(a), phases[i]-phases[a])} {scale(v(b), phases[i]-phases[b])})'
                expr = f'(call $quant {expr} (i32.const {phases[i]}))'
        code.append(f'(local.set {n+i} {expr})')
    kernel = f'''(func (param {' '.join(['f32']*n)}) (result f32)
      (local {' '.join(['f64']*len(nodes))}) {' '.join(code)}
      (f32.demote_f64 {scale(v(root), -phases[root])}))'''
    text = base.wrap(kernel, n)
    if mode != 'eager':
        text = text[:-1]+' '+quantizer()+')'
    return text, dict(mode=mode, scales=phases, nodes=len(nodes), arithmetic=sum(t[0]!='input' for t in nodes))


def transform(src, dst, mode='shifted', seed=37):
    t0 = time.perf_counter_ns()
    n, nodes, root = base.parse_source(q.read(src))
    t1 = time.perf_counter_ns()
    text, info = generate(n, nodes, root, mode, seed)
    t2 = time.perf_counter_ns()
    q.compile(text, dst)
    t3 = time.perf_counter_ns()
    return dict(**info, read_ms=(t1-t0)/1e6, generate_ms=(t2-t1)/1e6, compile_ms=(t3-t2)/1e6,
                total_ms=(t3-t0)/1e6)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--mode', choices=['plain','eager','grid0','shifted'], default='shifted')
    ap.add_argument('--seed', type=int, default=37)
    a = ap.parse_args()
    print(json.dumps(transform(a.src, a.dst, a.mode, a.seed)))
