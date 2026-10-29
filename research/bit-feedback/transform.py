"""Restricted real-Wasm transformer; a hypothesis, not a security claim."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import time

spec = importlib.util.spec_from_file_location('stack_cycle', Path(__file__).resolve().parents[1]/'stack-cycle/transform.py')
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
w = sc.w
OPS = {'add', 'sub', 'mul', 'xor', 'and', 'or', 'shl', 'shr_u', 'shr_s', 'rotl', 'rotr'}
SHIFTS = {'shl', 'shr_u', 'shr_s', 'rotl', 'rotr'}


def source(path):
    mod, decl, body, _, np, nl = sc.source(path)
    if any(x[0] not in ('type', 'func', 'export') for x in mod[1:]):
        raise ValueError('Pure module required')
    if any(v != 'i32' for x in decl if x[0] in ('param', 'local', 'result') for v in x[1:]):
        raise ValueError('i32 only')
    if [x for x in decl if x[0] == 'result'] != [['result', 'i32']]:
        raise ValueError('One i32 result required')
    env = [('p', i) for i in range(np)] + [('c', 0)] * nl
    stack = []; nodes = []
    for ins in body:
        op = ins[0]
        if op == 'nop': continue
        if op == 'drop': stack.pop(); continue
        if op == 'i32.const': stack.append(('c', int(ins[1]) & 0xffffffff)); continue
        if op == 'local.get': stack.append(env[int(ins[1])]); continue
        if op in ('local.set', 'local.tee'):
            env[int(ins[1])] = stack[-1]
            if op == 'local.set': stack.pop()
            continue
        name = op.removeprefix('i32.')
        if not op.startswith('i32.') or name not in OPS: raise ValueError('Unsupported op: '+op)
        b = stack.pop(); a = stack.pop()
        if name in SHIFTS and b[0] != 'c': raise ValueError('Variable shift unsupported')
        nodes.append((name, a, b)); stack.append(('n', len(nodes)-1))
    if len(stack) != 1 or not 1 <= len(nodes) <= 32: raise ValueError('Require 1..32 operation nodes')
    return mod, np, nodes, stack[0]


def depbits(node, bit, width):
    op, a, b = node
    if op in ('add', 'sub', 'mul'):
        return [(x, q) for x in (a, b) for q in range(bit+1)]
    if op in ('and', 'or', 'xor'): return [(a, bit), (b, bit)]
    k = b[1] % width
    if op == 'shl': return [(a, bit-k)] if bit >= k else []
    if op == 'shr_u': return [(a, bit+k)] if bit+k < width else []
    if op == 'shr_s': return [(a, min(bit+k, width-1))]
    if op == 'rotl': return [(a, (bit-k) % width)]
    if op == 'rotr': return [(a, (bit+k) % width)]
    raise ValueError(op)


def base_edges(nodes, width):
    return {(r[1]*width+q, i*width+b) for i, node in enumerate(nodes)
            for b in range(width) for r, q in depbits(node, b, width) if r[0] == 'n'}


def topology(size, edges):
    children = [[] for _ in range(size)]; indegree = [0]*size
    for a, b in edges: children[a].append(b); indegree[b] += 1
    todo = [i for i, d in enumerate(indegree) if d == 0]; depth = [1]*size
    order = []
    while todo:
        a = todo.pop(); order.append(a)
        for b in children[a]:
            depth[b] = max(depth[b], depth[a]+1); indegree[b] -= 1
            if not indegree[b]: todo.append(b)
    if len(order) != size: return None
    return order, max(depth, default=0)


def reachability(size, edges):
    order, _ = topology(size, edges)
    children = [[] for _ in range(size)]
    for a, b in edges: children[a].append(b)
    reach = [0]*size
    for a in reversed(order):
        for b in children[a]: reach[a] |= (1 << b) | reach[b]
    return reach


def plan(nodes, mode='masked', seed=20261018, width=32, extra_depth=16):
    edges = base_edges(nodes, width); size = len(nodes)*width
    base_depth = topology(size, edges)[1]; budget = base_depth+extra_depth
    candidates = [(i, j, k) for i in range(len(nodes)) for j in range(i+1, len(nodes))
                  for k in range(1, min(8, width))]
    rng = random.Random(seed); rng.shuffle(candidates)
    selected = []; rejected_cycle_bits = 0; rejected_depth = 0; tried = 0
    if mode != 'none':
        for i, j, k in candidates:
            if len(selected) >= min(12, len(nodes)): break
            tried += 1; reach = reachability(size, edges); proposed = set(); mask = 0
            for b in range(k, width):
                u, v = j*width+b-k, i*width+b
                if u == v or (reach[v] >> u) & 1:
                    rejected_cycle_bits += 1
                    if mode == 'uniform': mask = 0; proposed = set(); break
                    continue
                new_reach = (1 << v) | reach[v]
                for a in range(size):
                    if a == u or (reach[a] >> u) & 1: reach[a] |= new_reach
                proposed.add((u, v)); mask |= 1 << b
            if not mask: continue
            candidate_edges = edges | proposed
            candidate_depth = topology(size, candidate_edges)[1]
            if candidate_depth > budget: rejected_depth += 1; continue
            edges = candidate_edges; selected.append((i, j, k, mask))
    if mode not in ('none', 'uniform', 'masked'): raise ValueError('Unknown mode')
    return {'mode': mode, 'width': width, 'feedback': selected, 'rounds': topology(size, edges)[1],
            'base_rounds': base_depth, 'depth_budget': budget, 'proposals': tried,
            'cycle_bits_rejected': rejected_cycle_bits, 'depth_proposals_rejected': rejected_depth,
            'feedback_bits': sum(m.bit_count() if hasattr(int, 'bit_count') else bin(m).count('1') for _, _, _, m in selected)}


def emit(mod, np, nodes, result, p, rounds=None, initial=0):
    n = len(nodes); old = np; nxt = np+n; counter = np+2*n
    def ref(r):
        if r[0] == 'p': return f'(local.get {r[1]})'
        if r[0] == 'n': return f'(local.get {old+r[1]})'
        return f'(i32.const {r[1]})'
    def expr(i):
        op, a, b = nodes[i]; return f'(i32.{op} {ref(a)} {ref(b)})'
    parts = ['(func '+(' '.join('(param i32)' for _ in range(np)))+' (result i32)',
             '(local '+' '.join(['i32']*(2*n+1))+')']
    if initial:
        for i in range(n): parts.append(f'(local.set {old+i} (i32.const {initial & 0xffffffff}))')
    parts.append(f'(local.set {counter} (i32.const {rounds or p["rounds"]}))')
    parts.append('(loop $settle')
    for i in range(n):
        e = expr(i)
        for dest, j, k, mask in p['feedback']:
            if dest == i:
                residual = f'(i32.xor (local.get {old+j}) {expr(j)})'
                e = f'(i32.xor {e} (i32.and (i32.shl {residual} (i32.const {k})) (i32.const {mask})))'
        parts.append(f'(local.set {nxt+i} {e})')
    for i in range(n): parts.append(f'(local.set {old+i} (local.get {nxt+i}))')
    parts += [f'(local.set {counter} (i32.sub (local.get {counter}) (i32.const 1)))',
              f'(br_if $settle (local.get {counter}))', ')', ref(result), ')']
    fn = '\n'.join(parts)
    # Type references need not be preserved on the replacement function.
    return '(module\n'+'\n'.join(fn if x[0] == 'func' else w.emit(x) for x in mod[1:])+'\n)'


def calc(node, values, inputs, width=32):
    mask = (1 << width)-1
    def val(r): return (inputs[r[1]] if r[0] == 'p' else values[r[1]] if r[0] == 'n' else r[1]) & mask
    op, a, b = node; a, b = val(a), val(b); k = b % width
    if op == 'add': z = a+b
    elif op == 'sub': z = a-b
    elif op == 'mul': z = a*b
    elif op == 'xor': z = a ^ b
    elif op == 'and': z = a & b
    elif op == 'or': z = a | b
    elif op == 'shl': z = a << k
    elif op == 'shr_u': z = a >> k
    elif op == 'shr_s': z = (a-(1 << width) if a >> (width-1) else a) >> k
    elif op == 'rotl': z = (a << k) | (a >> ((width-k) % width))
    elif op == 'rotr': z = (a >> k) | (a << ((width-k) % width))
    else: raise ValueError(op)
    return z & mask


def transform(src, out, mode='masked', seed=20261018, initial=0, rounds=None):
    if out.exists(): raise ValueError('Refuse overwrite')
    start = time.perf_counter(); mod, np, nodes, result = source(src)
    p = plan(nodes, mode, seed); p.update({'nodes': len(nodes), 'seed': seed})
    text = emit(mod, np, nodes, result, p, rounds, initial)
    out.parent.mkdir(parents=True, exist_ok=True); wp = out.with_suffix('.wat'); wp.write_text(text, encoding='utf-8')
    w.tool('wat2wasm', [wp, '-o', out]); w.tool('wasm-validate', [out])
    p.update({'seconds': time.perf_counter()-start, 'actual_rounds': rounds or p['rounds'],
              'input_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
              'output_sha256': hashlib.sha256(out.read_bytes()).hexdigest(), 'initial': initial})
    Path(str(out)+'.json').write_text(json.dumps(p, indent=2), encoding='utf-8')
    return p


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('input', type=Path); ap.add_argument('output', type=Path)
    ap.add_argument('--mode', choices=('none', 'uniform', 'masked'), default='masked')
    ap.add_argument('--seed', type=int, default=20261018)
    a = ap.parse_args(); print(json.dumps(transform(a.input, a.output, a.mode, a.seed)))
