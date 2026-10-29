"""Binary-only fixed-point bit evaluator. No source, plan or seed input.

This normalizes a restricted Boolean DAG, not arbitrary equivalent formulas.
Unsupported syntax and actual dependency cycles are reported separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import transform as t


def expressions(path):
    t.w.tool('wasm-validate', [path])
    mod = t.w.parse(t.w.tool('wasm2wat', [path, '--fold-exprs', '--no-debug-names']))
    if any(x[0] not in ('type', 'func', 'export') for x in mod[1:]): raise ValueError('Unsupported module')
    funcs = [x for x in mod[1:] if x[0] == 'func']
    if len(funcs) != 1: raise ValueError('One function required')
    fn = funcs[0]; decl = [x for x in fn[1:] if isinstance(x, list) and x[0] in ('type', 'local', 'param', 'result')]
    np = sum(len(x)-1 for x in decl if x[0] == 'param'); nl = sum(len(x)-1 for x in decl if x[0] == 'local')
    if any(v != 'i32' for x in decl if x[0] in ('param', 'local', 'result') for v in x[1:]): raise ValueError('i32 only')
    body = [x for x in fn[1:] if x not in decl]
    env = [('p', i) for i in range(np)] + [('c', 0)]*nl
    equations = {}; loops = 0; stack = []; guards = []; rounds = None
    def execute(instructions):
        for ins in instructions:
            op = ins[0]
            if op == 'nop': continue
            if op == 'local.get': stack.append(env[int(ins[1])]); continue
            if op == 'i32.const': stack.append(('c', int(ins[1]) & 0xffffffff)); continue
            if op in ('local.set', 'local.tee'):
                env[int(ins[1])] = stack[-1]
                if op == 'local.set': stack.pop()
                continue
            if op == 'drop': stack.pop(); continue
            if op == 'br_if': guards.append(stack.pop()); continue
            name = op.removeprefix('i32.')
            if op == 'i32.eqz': stack.append(('eqz', stack.pop())); continue
            if op.startswith('i32.') and name in t.OPS:
                b, a = stack.pop(), stack.pop()
                if name in t.SHIFTS and b[0] != 'c': raise ValueError('Variable shift')
                stack.append((name, a, b)); continue
            raise ValueError('Unsupported instruction '+str(ins))
    for x in body:
        if isinstance(x, list) and x[0] == 'loop':
            loops += 1
            if loops > 1: raise ValueError('Multiple loops')
            seq = [y for y in x[1:] if not (isinstance(y, str) and y.startswith('$'))]
            if not seq or not isinstance(seq[-1], list) or seq[-1][0:2] != ['br_if', '0']:
                raise ValueError('Expected final back edge to loop')
            if any(isinstance(y, list) and y[0] in ('block', 'loop', 'if', 'br', 'br_if') for y in seq[:-1]):
                raise ValueError('Control in loop body')
            initial_env = list(env)
            env[:] = [('p', i) for i in range(np)] + [('v', i) for i in range(np, np+nl)]
            if stack: raise ValueError('Live stack at loop entry unsupported')
            for y in seq: execute(t.sc.flat(y))
            if stack: raise ValueError('Loop with stack results unsupported')
            equations = {i: e for i, e in enumerate(env) if i >= np and e != ('v', i)}
            guard = guards[-1]
            if not (guard[0] == 'sub' and guard[1][0] == 'v' and guard[2] == ('c', 1)):
                raise ValueError('Expected simple decreasing loop counter')
            counter = guard[1][1]
            if equations.get(counter) != guard or initial_env[counter][0] != 'c' or not initial_env[counter][1]:
                raise ValueError('Expected nonzero constant loop count')
            rounds = initial_env[counter][1]
            env[:] = [('p', i) for i in range(np)] + [('v', i) for i in range(np, np+nl)]
        else:
            execute(t.sc.flat(x))
    if len(stack) != 1: raise ValueError('Expected one result')
    return np, stack[0], equations, rounds


class Bits:
    def __init__(self, equations):
        self.eq = equations; self.gates = [('c', 0), ('c', 1)]; self.index = {x:i for i,x in enumerate(self.gates)}
        self.memo = {}; self.active = set(); self.requests = 0; self.ranks = {}; self.levels = []
    def intern(self, g):
        if g not in self.index: self.index[g] = len(self.gates); self.gates.append(g)
        return self.index[g]
    def xor(self, *args):
        terms = set()
        for a in args:
            if a == 0: continue
            group = self.gates[a][1:] if self.gates[a][0] == 'xor' else (a,)
            for b in group:
                if b in terms: terms.remove(b)
                else: terms.add(b)
        if not terms: return 0
        if len(terms) == 1: return next(iter(terms))
        return self.intern(('xor', *sorted(terms)))
    def and_(self, a, b):
        if not a or not b: return 0
        if a == 1: return b
        if b == 1 or a == b: return a
        return self.intern(('and', *sorted((a, b))))
    def add(self, a, b, carry=0):
        out = []
        for x, y in zip(a, b):
            p = self.xor(x, y); out.append(self.xor(p, carry))
            carry = self.xor(self.and_(x, y), self.and_(p, carry))
        return out
    def bit(self, e, b):
        self.requests += 1; key = (e, b)
        if key in self.memo:
            if self.levels: self.levels[-1] = max(self.levels[-1], self.ranks[key])
            return self.memo[key]
        if key in self.active: raise RuntimeError('bit_dependency_cycle')
        self.active.add(key); self.levels.append(0); op = e[0]
        if op == 'c': z = (e[1] >> b) & 1
        elif op == 'p': z = self.intern(('input', e[1], b))
        elif op == 'v':
            if e[1] not in self.eq: raise ValueError('Unchanged state local')
            z = self.bit(self.eq[e[1]], b)
        elif op in t.SHIFTS:
            k = e[2][1] % 32
            q = {'shl': b-k, 'shr_u': b+k, 'shr_s': min(b+k, 31), 'rotl': (b-k)%32, 'rotr': (b+k)%32}[op]
            z = self.bit(e[1], q) if 0 <= q < 32 else 0
        elif op == 'and' and (e[1][0] == 'c' or e[2][0] == 'c'):
            c, other = (e[1], e[2]) if e[1][0] == 'c' else (e[2], e[1])
            z = self.bit(other, b) if (c[1] >> b) & 1 else 0
        elif op in ('xor', 'and', 'or'):
            a, c = self.bit(e[1], b), self.bit(e[2], b)
            z = self.xor(a, c) if op == 'xor' else self.and_(a, c) if op == 'and' else self.xor(a, c, self.and_(a, c))
        elif op in ('add', 'sub', 'mul'):
            # Only the required low prefix is requested; higher bits may depend on this bit.
            a = [self.bit(e[1], i) for i in range(b+1)]; c = [self.bit(e[2], i) for i in range(b+1)]
            if op == 'add': z = self.add(a, c)[b]
            elif op == 'sub': z = self.add(a, [self.xor(x, 1) for x in c], 1)[b]
            else:
                out = [0]*(b+1)
                for j in range(b+1):
                    row = [0]*j + [self.and_(a[i-j], c[j]) for i in range(j, b+1)]
                    out = self.add(out, row)
                z = out[b]
        else: raise ValueError('Unknown operation '+op)
        self.active.remove(key); self.memo[key] = z
        self.ranks[key] = self.levels.pop() + (1 if op == 'v' else 0)
        if self.levels: self.levels[-1] = max(self.levels[-1], self.ranks[key])
        if len(self.gates) > 250000: raise ValueError('Boolean gate budget exceeded')
        return z
    def digest(self, roots):
        memo = {}
        def visit(i):
            if i in memo: return memo[i]
            g = self.gates[i]
            payload = list(g) if g[0] in ('c', 'input') else [g[0], *sorted(visit(j) for j in g[1:])]
            memo[i] = hashlib.sha256(json.dumps(payload).encode()).hexdigest(); return memo[i]
        result = [visit(i) for i in roots]
        return result, set(memo)
    def wat(self, np, roots):
        _, live = self.digest(roots); live = sorted(live); slots = {i:np+k for k,i in enumerate(live)}
        parts = ['(module (func (export "run") '+(' '.join('(param i32)' for _ in range(np)))+' (result i32)',
                 '(local '+' '.join('i32' for _ in live)+')']
        get = lambda i: f'(local.get {slots[i]})'
        for i in live:
            g = self.gates[i]
            if g[0] == 'c': e = f'(i32.const {g[1]})'
            elif g[0] == 'input': e = f'(i32.and (i32.shr_u (local.get {g[1]}) (i32.const {g[2]})) (i32.const 1))'
            else:
                e = get(g[1])
                for j in g[2:]: e = f'(i32.{g[0]} {e} {get(j)})'
            parts.append(f'(local.set {slots[i]} {e})')
        e = '(i32.const 0)'
        for b, i in enumerate(roots): e = f'(i32.or {e} (i32.shl {get(i)} (i32.const {b})))'
        return '\n'.join(parts+[e, '))'])


def recover(path, output=None):
    start = time.perf_counter(); np, expr, eq, rounds = expressions(path); parsed = time.perf_counter()
    engine = Bits(eq); roots = [engine.bit(expr, b) for b in range(32)]
    bound = max(engine.ranks[(expr,b)] for b in range(32))
    if rounds is not None and bound > rounds: raise RuntimeError('insufficient_round_bound')
    digests, live = engine.digest(roots); end = time.perf_counter()
    report = {'status': 'ok', 'parse_seconds': parsed-start, 'solve_seconds': end-parsed,
              'seconds': end-start, 'state_equations': len(eq), 'visited_bits': len(engine.memo),
              'requests': engine.requests, 'created_gates': len(engine.gates), 'live_gates': len(live), 'digest': digests,
              'verified_rounds': rounds, 'output_settling_bound': bound}
    if output:
        if output.exists(): raise ValueError('Refuse overwrite')
        wp = output.with_suffix('.wat'); wp.write_text(engine.wat(np, roots), encoding='utf-8')
        t.w.tool('wat2wasm', [wp, '-o', output]); t.w.tool('wasm-validate', [output])
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('input', type=Path); ap.add_argument('--output', type=Path)
    a = ap.parse_args(); print(json.dumps(recover(a.input, a.output)))
