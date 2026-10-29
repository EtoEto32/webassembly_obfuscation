"""Restricted radial Hasse-coefficient experiment; no novelty/security claim."""
import argparse
import importlib.util
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('hasse_tools', ROOT/'research/isotope-swizzle/prototype.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
MASK = (1 << 32) - 1


class Unsupported(ValueError):
    pass


class DAG:
    def __init__(self):
        self.nodes = []
        self.cache = {}

    def node(self, *v):
        v = tuple(v)
        if v not in self.cache:
            self.cache[v] = len(self.nodes)
            self.nodes.append(v)
        return self.cache[v]

    def const(self, v):
        return self.node('c', v & MASK)

    def op(self, op, a, b):
        x, y = self.nodes[a], self.nodes[b]
        if x[0] == y[0] == 'c':
            return self.const({'add': lambda: x[1]+y[1], 'sub': lambda: x[1]-y[1], 'mul': lambda: x[1]*y[1]}[op]())
        if op == 'mul':
            if x == ('c', 0) or y == ('c', 0): return self.const(0)
            if x == ('c', 1): return b
            if y == ('c', 1): return a
        if op == 'add':
            if x == ('c', 0): return b
            if y == ('c', 0): return a
        if op == 'sub' and y == ('c', 0): return a
        return self.node(op, a, b)


def read(path, attack=False):
    mod = q.read(path)
    if any(e[0] not in ('type', 'func', 'export') for e in mod[1:]):
        raise Unsupported('pure module only')
    fs = [e for e in mod[1:] if e[0] == 'func']
    if len(fs) != 1 or [e for e in mod[1:] if e[0] == 'export'] != [['export', '"run"', ['func', '0']]]:
        raise Unsupported('one run function required')
    f = fs[0]
    types = {k: [t for e in f[1:] if e[0] == k for t in e[1:]] for k in ('param', 'result', 'local')}
    if types['param'] != ['i32', 'i32'] or types['result'] != ['i32'] or any(t != 'i32' for t in types['local']):
        raise Unsupported('i32,i32 -> i32 required')
    dag = DAG()
    env = [dag.node('x', 0), dag.node('x', 1)] + [dag.const(0)] * len(types['local'])

    def walk(e):
        op = e[0]
        if op == 'i32.const': return dag.const(int(e[1], 0))
        if op == 'local.get': return env[int(e[1])]
        if op in ('local.set', 'local.tee'):
            value = walk(e[2]); env[int(e[1])] = value
            return value if op == 'local.tee' else None
        if op == 'block':
            value = None
            for child in e[1:]:
                if not isinstance(child, list): raise Unsupported('labelled block')
                if child[0] not in ('result', 'type'): value = walk(child)
            return value
        if op in ('i32.add', 'i32.sub', 'i32.mul'):
            return dag.op(op[4:], walk(e[1]), walk(e[2]))
        if attack and op == 'i32.shl':
            a, b = walk(e[1]), walk(e[2])
            if dag.nodes[b][0] != 'c': raise Unsupported('dynamic shift')
            return dag.op('mul', a, dag.const(1 << (dag.nodes[b][1] & 31)))
        raise Unsupported('instruction: '+op)

    root = None
    for e in f[1:]:
        if e[0] not in ('type', 'param', 'result', 'local'): root = walk(e)
    if root is None: raise Unsupported('missing result')
    return dag, root


def emit(dag, root):
    body, locations = [], {}

    def visit(i):
        n = dag.nodes[i]
        if n[0] == 'x': return ['local.get', str(n[1])]
        if n[0] == 'c': return ['i32.const', str(n[1])]
        if i not in locations:
            a, b = visit(n[1]), visit(n[2])
            locations[i] = 2 + len(locations)
            body.append(['local.set', str(locations[i]), ['i32.'+n[0], a, b]])
        return ['local.get', str(locations[i])]

    out = visit(root)
    f = ['func', ['export', '"run"'], ['param', 'i32', 'i32'], ['result', 'i32']]
    if locations: f.append(['local', *(['i32']*len(locations))])
    return q.w.emit(['module', [*f, *body, out]])


def degree(dag, root):
    memo = {}
    def go(i):
        if i in memo: return memo[i]
        n = dag.nodes[i]
        if n[0] == 'c': d = 0
        elif n[0] == 'x': d = 1
        else:
            a, b = go(n[1]), go(n[2])
            if n[0] == 'mul': d = a+b
            elif a == b: d = a
            else: raise Unsupported('syntactically inhomogeneous sum')
        if d > 4096: raise Unsupported('degree budget')
        memo[i] = d
        return d
    return go(root)


def transform(src, dst, k):
    start = time.perf_counter()
    dag, root = read(src)
    d = degree(dag, root)
    if not 1 <= k <= min(d, 32): raise Unsupported('coefficient order outside 1..min(d,32)')
    factor = math.comb(d, k) & MASK
    if factor % 2 == 0: raise Unsupported('non-unit binomial factor')
    out = DAG(); memo = {}
    def jet(i, j):
        if (i, j) in memo: return memo[i, j]
        n = dag.nodes[i]
        if n[0] == 'x': v = out.node(*n) if j <= 1 else out.const(0)
        elif n[0] == 'c': v = out.const(n[1] if j == 0 else 0)
        elif n[0] in ('add', 'sub'): v = out.op(n[0], jet(n[1], j), jet(n[2], j))
        else:
            v = out.const(0)
            for a in range(j+1):
                v = out.op('add', v, out.op('mul', jet(n[1], a), jet(n[2], j-a)))
        memo[i, j] = v
        return v
    answer = out.op('mul', out.const(pow(factor, -1, 1 << 32)), jet(root, k))
    built = time.perf_counter()
    q.compile(emit(out, answer), dst)
    return dict(degree=d, order=k, factor=factor, source_nodes=len(dag.nodes), jet_nodes=len(out.nodes),
                coefficient_requests=len(memo), read_build_ms=(built-start)*1000,
                transform_ms=(time.perf_counter()-start)*1000)


def polynomial(dag, root):
    memo = {}; products = 0
    def go(i):
        nonlocal products
        if i in memo: return memo[i]
        n = dag.nodes[i]
        if n[0] == 'c': p = {(0, 0): n[1]} if n[1] else {}
        elif n[0] == 'x': p = {(1, 0) if n[1] == 0 else (0, 1): 1}
        else:
            a, b = go(n[1]), go(n[2]); p = {}
            if n[0] == 'mul':
                for (i1,j1), c1 in a.items():
                    for (i2,j2), c2 in b.items():
                        key = i1+i2, j1+j2
                        p[key] = (p.get(key, 0)+c1*c2) & MASK
                        products += 1
            else:
                p = dict(a); sign = 1 if n[0] == 'add' else -1
                for key, val in b.items(): p[key] = (p.get(key, 0)+sign*val) & MASK
            p = {key: val for key, val in p.items() if val}
        if len(p) > 4096 or any(sum(key) > 4096 for key in p): raise Unsupported('polynomial budget')
        memo[i] = p
        return p
    p = go(root)
    return p, dict(visited_nodes=len(memo), coefficient_products=products, terms=len(p))


def horner(poly):
    dag = DAG(); x = dag.node('x',0); y = dag.node('x',1); zero = dag.const(0)
    rows = {}
    for (i,j),c in poly.items(): rows.setdefault(i,{})[j] = c
    answer = zero
    for i in range(max(rows,default=0),-1,-1):
        row = rows.get(i,{}); part = zero
        for j in range(max(row,default=0),-1,-1): part = dag.op('add',dag.op('mul',part,y),dag.const(row.get(j,0)))
        answer = dag.op('add',dag.op('mul',answer,x),part)
    return emit(dag,answer)


def recover(src, dst):
    start = time.perf_counter(); dag, root = read(src, attack=True); loaded = time.perf_counter()
    samples=[]; p=None; stats=None
    for _ in range(11):
        t=time.perf_counter(); p,stats=polynomial(dag,root); samples.append((time.perf_counter()-t)*1000)
    q.compile(horner(p),dst)
    return dict(read_ms=(loaded-start)*1000, normalize_samples_ms=samples, **stats,
                coefficients=[[i,j,c] for (i,j),c in sorted(p.items())])


if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('action',choices=['transform','recover']); ap.add_argument('source'); ap.add_argument('output'); ap.add_argument('--order',type=int,default=1)
    a=ap.parse_args()
    result=transform(a.source,a.output,a.order) if a.action=='transform' else recover(a.source,a.output)
    q.save(str(a.output)+'.json',result)
