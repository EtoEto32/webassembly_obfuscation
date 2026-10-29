"""Restricted Wasm bitwise formula -> switching network -> Wasm.

The switching algebra and node elimination are known. This is a research
prototype, not a claim of a new secure obfuscation primitive.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import struct
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(os.environ.get('WASM_TOOLS_ROOT', ROOT / '.tools'))
WABT = TOOLS / 'wabt-1.0.42/bin'
BINARYEN = TOOLS / 'binaryen-version_133/bin'
MASK = 0xffffffff
MAGIC = 0x31474342  # BCG1, public format identification; not a secret.


def tool(name, args):
    folder = BINARYEN if name == 'wasm-opt' else WABT
    r = subprocess.run([str(folder / (name + '.exe')), *map(str, args)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode:
        raise RuntimeError(json.dumps({'command': [name, *map(str, args)],
                                      'stdout': r.stdout, 'stderr': r.stderr}))
    return r.stdout


def parse(text):
    # Only WABT-generated folded text. WABT's comments are non-nested indices.
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|;;[^\n]*|\(;[\s\S]*?;\)|[()]|[^\s()]+', text)
    tokens = [t for t in tokens if not t.startswith((';;', '(;'))]
    pos = 0
    def one():
        nonlocal pos
        t = tokens[pos]
        pos += 1
        if t != '(':
            return t
        out = []
        while tokens[pos] != ')':
            out.append(one())
        pos += 1
        return out
    result = one()
    if pos != len(tokens) or result[0] != 'module':
        raise ValueError('Not a single folded module')
    return result


def emit(t):
    return '(' + ' '.join(map(emit, t)) + ')' if isinstance(t, list) else str(t)


def source(src):
    tool('wasm-validate', [src])
    mod = parse(tool('wasm2wat', [src, '--fold-exprs']))
    if any(x[0] not in ('type', 'func', 'export') for x in mod[1:]):
        raise ValueError('Only types, one function and one export are supported')
    funcs = [x for x in mod[1:] if x[0] == 'func']
    exports = [x for x in mod[1:] if x[0] == 'export']
    if len(funcs) != 1 or len(exports) != 1 or exports[0][2] != ['func', '0']:
        raise ValueError('Expected exactly one exported function')
    f = funcs[0]
    params = [p for x in f[1:] if isinstance(x, list) and x[0] == 'param' for p in x[1:]]
    if not (1 <= len(params) <= 128) or any(p != 'i32' for p in params):
        raise ValueError('Expected unnamed i32 parameters in WABT output')
    if [x for x in f[1:] if isinstance(x, list) and x[0] == 'result'] != [['result', 'i32']]:
        raise ValueError('Expected one i32 result')
    body = [x for x in f[1:] if isinstance(x, list) and x[0] not in ('type', 'param', 'result')]
    if len(body) != 1:
        raise ValueError('Expected a single expression, with no locals')
    def walk(x):
        op = x[0]
        if op == 'local.get' and len(x) == 2 and 0 <= int(x[1]) < len(params):
            return ('var', int(x[1]))
        if op == 'i32.const' and len(x) == 2 and (int(x[1]) & MASK) in (0, MASK):
            return ('const', int(x[1]) & MASK)
        if op in ('i32.and', 'i32.or', 'i32.xor') and len(x) == 3:
            return (op[4:], walk(x[1]), walk(x[2]))
        raise ValueError('Unsupported formula: ' + emit(x))
    return len(params), exports[0][1], walk(body[0])


def formula_wat(t):
    if t[0] == 'var':
        return f'(local.get {t[1]})'
    if t[0] == 'const':
        return '(i32.const -1)' if t[1] else '(i32.const 0)'
    return f'(i32.{t[0]} {formula_wat(t[1])} {formula_wat(t[2])})'


def plain_wat(n, name, t):
    return f'(module (func (export {name}) (param {" ".join(["i32"] * n)}) (result i32) {formula_wat(t)}))'


class Labels:
    def __init__(self):
        self.nodes = []
        self.index = {}
        self.zero = self.intern((1, 0, 0))
        self.one = self.intern((1, MASK, 0))

    def intern(self, record):
        if record not in self.index:
            self.index[record] = len(self.nodes)
            self.nodes.append(record)
        return self.index[record]

    def var(self, i):
        return self.intern((0, i, 0))

    def binary(self, op, a, b):
        if a > b:
            a, b = b, a
        if a == b:
            return self.zero if op == 4 else a
        if op == 2:
            if self.zero in (a, b):
                return self.zero
            if self.one in (a, b):
                return b if a == self.one else a
        if op == 3:
            if self.one in (a, b):
                return self.one
            if self.zero in (a, b):
                return b if a == self.zero else a
        if op == 4 and self.zero in (a, b):
            return b if a == self.zero else a
        return self.intern((op, a, b))


def network(t, fraction, seed=20261018):
    labels = Labels()
    adjacency = {0: {}, 1: {}}
    separators = []
    def vertex():
        v = len(adjacency)
        adjacency[v] = {}
        return v
    def edge(a, b, value):
        old = adjacency[a].get(b, labels.zero)
        new = labels.binary(3, old, value)
        if new != labels.zero:
            adjacency[a][b] = adjacency[b][a] = new
    def build(expr, a, b, invert=False):
        op = expr[0]
        if op in ('var', 'const'):
            value = labels.var(expr[1]) if op == 'var' else (labels.one if expr[1] else labels.zero)
            if invert:
                value = labels.binary(4, value, labels.one)
            edge(a, b, value)
            return
        x, y = expr[1:]
        if op == 'xor':
            # XOR: x & !y OR !x & y. XNOR toggles the second operand.
            m, q = vertex(), vertex()
            separators.extend((m, q))
            build(x, a, m, False)
            build(y, m, b, not invert)
            build(x, a, q, True)
            build(y, q, b, invert)
        elif (op == 'and') != invert:
            m = vertex()
            separators.append(m)
            build(x, a, m, invert)
            build(y, m, b, invert)
        else:
            build(x, a, b, invert)
            build(y, a, b, invert)
    build(t, 0, 1)
    initial_vertices = len(adjacency)
    if initial_vertices > 1024:
        raise ValueError('Graph expansion exceeds prototype limit')
    rng = random.Random(seed)
    # All non-terminal vertices here originate at formula composition sites.
    order = list(dict.fromkeys(separators))
    rng.shuffle(order)
    removed = order[:math.floor(fraction * len(order))]
    for k in removed:
        neighbors = list(adjacency[k].items())
        for index, (a, av) in enumerate(neighbors):
            for b, bv in neighbors[index + 1:]:
                edge(a, b, labels.binary(2, av, bv))
        for a, _ in neighbors:
            del adjacency[a][k]
        del adjacency[k]
    vertices = list(adjacency)
    rng.shuffle(vertices)
    rename = {v: i for i, v in enumerate(vertices)}
    edges = [(rename[a], rename[b], value) for a, dests in adjacency.items()
             for b, value in dests.items() if a < b]
    rng.shuffle(edges)
    # Prune labels no longer used by any remaining edge.
    needed = set()
    def visit(node):
        if node in needed:
            return
        needed.add(node)
        op, a, b = labels.nodes[node]
        if op >= 2:
            visit(a)
            visit(b)
    for _, _, value in edges:
        visit(value)
    ids = sorted(needed)
    ids_map = {v: i for i, v in enumerate(ids)}
    nodes = []
    for v in ids:
        op, a, b = labels.nodes[v]
        nodes.append((op, ids_map[a], ids_map[b]) if op >= 2 else (op, a, b))
    edges = [(a, b, ids_map[v]) for a, b, v in edges]
    return {'nodes': nodes, 'edges': edges, 'vertices': len(vertices), 's': rename[0], 't': rename[1],
            'initial_vertices': initial_vertices, 'removed_vertices': len(removed)}


def graph_wat(n, name, graph):
    nodes, edges = graph['nodes'], graph['edges']
    nb = 52
    eb = nb + 12 * len(nodes)
    ib = eb + 12 * len(edges)
    vb = ib + 4 * n
    rb = vb + 4 * len(nodes)
    header = [MAGIC, 1, n, len(nodes), graph['vertices'], len(edges), graph['s'], graph['t'], nb, eb, ib, vb, rb]
    words = header + [v for row in nodes + edges for v in row]
    data = struct.pack('<' + 'I' * len(words), *words)
    pages = max(1, math.ceil((rb + 4 * graph['vertices']) / 65536))
    encoded = ''.join('\\%02x' % b for b in data)
    params = ' '.join(['i32'] * n)
    initialization = '\n'.join(f'(i32.store (i32.const {ib + 4*i}) (local.get {i}))' for i in range(n))
    wat = f'''(module
      (memory {pages} {pages})
      (data (i32.const 0) "{encoded}")
      (func (export {name}) (param {params}) (result i32)
        (local $i i32) (local $p i32) (local $op i32) (local $a i32) (local $b i32)
        (local $z i32) (local $u i32) (local $v i32) (local $mask i32) (local $round i32)
        {initialization}
        (local.set $i (i32.const 0))
        (block $nodes_done (loop $nodes
          (br_if $nodes_done (i32.ge_u (local.get $i) (i32.const {len(nodes)})))
          (local.set $p (i32.add (i32.const {nb}) (i32.mul (local.get $i) (i32.const 12))))
          (local.set $op (i32.load (local.get $p)))
          (local.set $a (i32.load offset=4 (local.get $p)))
          (local.set $b (i32.load offset=8 (local.get $p)))
          (if (i32.eqz (local.get $op))
            (then (local.set $z (i32.load (i32.add (i32.const {ib}) (i32.shl (local.get $a) (i32.const 2))))))
            (else (if (i32.eq (local.get $op) (i32.const 1))
              (then (local.set $z (local.get $a)))
              (else
                (local.set $a (i32.load (i32.add (i32.const {vb}) (i32.shl (local.get $a) (i32.const 2)))))
                (local.set $b (i32.load (i32.add (i32.const {vb}) (i32.shl (local.get $b) (i32.const 2)))))
                (local.set $z (if (result i32) (i32.eq (local.get $op) (i32.const 2))
                  (then (i32.and (local.get $a) (local.get $b)))
                  (else (if (result i32) (i32.eq (local.get $op) (i32.const 3))
                    (then (i32.or (local.get $a) (local.get $b)))
                    (else (i32.xor (local.get $a) (local.get $b)))))))))))
          (i32.store (i32.add (i32.const {vb}) (i32.shl (local.get $i) (i32.const 2))) (local.get $z))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $nodes)))
        (memory.fill (i32.const {rb}) (i32.const 0) (i32.const {4 * graph['vertices']}))
        (i32.store (i32.const {rb + 4 * graph['s']}) (i32.const -1))
        (local.set $round (i32.const 0))
        (block $done (loop $rounds
          (br_if $done (i32.ge_u (local.get $round) (i32.const {graph['vertices'] - 1})))
          (local.set $i (i32.const 0))
          (block $edges_done (loop $edges
            (br_if $edges_done (i32.ge_u (local.get $i) (i32.const {len(edges)})))
            (local.set $p (i32.add (i32.const {eb}) (i32.mul (local.get $i) (i32.const 12))))
            (local.set $u (i32.add (i32.const {rb}) (i32.shl (i32.load (local.get $p)) (i32.const 2))))
            (local.set $v (i32.add (i32.const {rb}) (i32.shl (i32.load offset=4 (local.get $p)) (i32.const 2))))
            (local.set $mask (i32.load (i32.add (i32.const {vb}) (i32.shl (i32.load offset=8 (local.get $p)) (i32.const 2)))))
            (i32.store (local.get $v) (i32.or (i32.load (local.get $v)) (i32.and (local.get $mask) (i32.load (local.get $u)))))
            (i32.store (local.get $u) (i32.or (i32.load (local.get $u)) (i32.and (local.get $mask) (i32.load (local.get $v)))))
            (local.set $i (i32.add (local.get $i) (i32.const 1)))
            (br $edges)))
          (local.set $round (i32.add (local.get $round) (i32.const 1)))
          (br $rounds)))
        (i32.load (i32.const {rb + 4 * graph['t']}))))'''
    return wat, pages


def transform(src, out, fraction):
    if out.exists() or Path(str(out) + '.json').exists():
        raise ValueError('Refuse overwrite')
    start = time.perf_counter()
    n, name, tree = source(src)
    graph = network(tree, fraction)
    if len(graph['nodes']) > 100000 or len(graph['edges']) > 100000:
        raise ValueError('Descriptor exceeds prototype budget')
    wat, pages = graph_wat(n, name, graph)
    out.parent.mkdir(parents=True, exist_ok=True)
    wp = Path(str(out) + '.wat')
    wp.write_text(wat, encoding='utf-8')
    tool('wat2wasm', [wp, '-o', out])
    tool('wasm-validate', [out])
    report = {k: graph[k] for k in ('initial_vertices', 'vertices', 'removed_vertices')}
    report.update({'labels': len(graph['nodes']), 'edges': len(graph['edges']), 'pages': pages,
                   'fraction': fraction, 'seconds': time.perf_counter() - start,
                   'input_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
                   'output_sha256': hashlib.sha256(out.read_bytes()).hexdigest()})
    Path(str(out) + '.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('input', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--fraction', type=float, choices=[0, 0.5, 0.8], default=0.5)
    a = ap.parse_args()
    print(json.dumps(transform(a.input, a.output, a.fraction)))
