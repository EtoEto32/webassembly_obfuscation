"""Exact polynomial profiles and bounded equivalent-tree generation.

Research prototype: pure i32 add/sub/mul only. No security claim.
"""
from collections import deque
import json

MASK = (1 << 32) - 1
OPS = ('add', 'sub', 'mul')
MAX_TERMS = 512


def key(tree):
    return json.dumps(tree, separators=(',', ':'))


def cost(tree):
    return 0 if not isinstance(tree, list) else 1 + cost(tree[1]) + cost(tree[2])


def poly_op(op, a, b):
    """Monomial is a sorted tuple of variable names, allowing repeated names."""
    out = dict(a) if op != 'mul' else {}
    if op == 'mul':
        for x, cx in a.items():
            for y, cy in b.items():
                m = tuple(sorted(x + y))
                out[m] = (out.get(m, 0) + cx * cy) & MASK
                if len(out) > MAX_TERMS:
                    raise ValueError('Polynomial term limit')
    else:
        sign = 1 if op == 'add' else -1
        for m, c in b.items():
            out[m] = (out.get(m, 0) + sign*c) & MASK
    return {m: c for m, c in out.items() if c}


def polynomial(tree):
    if isinstance(tree, int):
        return {(): tree & MASK} if tree & MASK else {}
    if isinstance(tree, str):
        return {(tree,): 1}
    op, a, b = tree
    if op not in OPS:
        raise ValueError('Unsupported polynomial operation')
    return poly_op(op, polynomial(a), polynomial(b))


def pkey(p):
    return tuple(sorted(p.items()))


def profile(tree):
    seen = set()
    def walk(t):
        if isinstance(t, list):
            walk(t[1]); walk(t[2])
            seen.add(pkey(polynomial(t)))
    walk(tree)
    return {'output': pkey(polynomial(tree)), 'observations': frozenset(seen), 'cost': cost(tree)}


def dominates(a, b):
    return (a['output'] == b['output'] and a['cost'] <= b['cost']
            and a['observations'] <= b['observations'])


def local_rules(t):
    if not isinstance(t, list):
        return
    op, a, b = t
    if op in ('add', 'mul'):
        yield [op, b, a]
        if isinstance(a, list) and a[0] == op:
            yield [op, a[1], [op, a[2], b]]
        if isinstance(b, list) and b[0] == op:
            yield [op, [op, a, b[1]], b[2]]
    if op == 'mul':
        if isinstance(a, list) and a[0] in ('add', 'sub'):
            yield [a[0], ['mul', a[1], b], ['mul', a[2], b]]
        if isinstance(b, list) and b[0] in ('add', 'sub'):
            yield [b[0], ['mul', a, b[1]], ['mul', a, b[2]]]
    if op in ('add', 'sub') and isinstance(a, list) and isinstance(b, list) and a[0] == b[0] == 'mul':
        for i in (1, 2):
            for j in (1, 2):
                if a[i] == b[j]:
                    yield ['mul', a[i], [op, a[3-i], b[3-j]]]
    if op == 'sub':
        yield ['add', a, ['mul', -1, b]]


def neighbors(t):
    if not isinstance(t, list):
        return
    yield from local_rules(t)
    for child in (1, 2):
        for n in neighbors(t[child]):
            r = list(t); r[child] = n
            yield r


def generate(source, limit=96, depth=3, cost_ratio=2):
    """Bounded BFS. Equivalence checked exactly; incomplete by construction."""
    source_poly = pkey(polynomial(source))
    queue = deque([(source, 0)])
    bank = {key(source): source}
    skipped_cost = 0
    attempted = 0
    budget_hit = False
    while queue:
        tree, d = queue.popleft()
        if d == depth:
            continue
        for n in neighbors(tree):
            attempted += 1
            if cost(n) > max(1, cost(source))*cost_ratio:
                skipped_cost += 1; continue
            k = key(n)
            if k in bank:
                continue
            if pkey(polynomial(n)) != source_poly:
                raise AssertionError(('Unsound rewrite', tree, n))
            if len(bank) >= limit:
                budget_hit = True; break
            bank[k] = n; queue.append((n, d+1))
        if budget_hit:
            break
    return list(bank.values()), {'attempted': attempted, 'retained': len(bank),
                                'cost_rejected': skipped_cost, 'budget_hit': budget_hit,
                                'depth': depth, 'limit': limit}


def frontier(trees):
    keep = []
    for t in trees:
        p = profile(t)
        if any(dominates(q, p) for _, q in keep):
            continue
        keep = [(old, q) for old, q in keep if not dominates(p, q)]
        keep.append((t, p))
    return [t for t, _ in keep]


def target(source):
    """Freeze largest nontrivial proper subtree, lexicographic tie break."""
    options = []
    out = pkey(polynomial(source))
    def walk(t, root=False):
        if not isinstance(t, list):
            return
        if not root and cost(t) >= 2 and pkey(polynomial(t)) != out:
            options.append(t)
        walk(t[1]); walk(t[2])
    walk(source, True)
    return sorted(options, key=lambda t: (-cost(t), key(t)))[0] if options else None


def atoms(tree):
    result = {pkey(polynomial(0)): 0, pkey(polynomial(1)): 1}
    def walk(t):
        if isinstance(t, list):
            walk(t[1]); walk(t[2])
        result.setdefault(pkey(polynomial(t)), t)
    walk(tree)
    return result


def recover_one(tree, wanted):
    """Exact algebraic 0/1-op observer, not full instruction-aware analysis."""
    ts = pkey(polynomial(wanted)); bank = atoms(tree)
    if ts in bank:
        return {'cost': 0, 'expression': bank[ts]}
    for a, at in bank.items():
        for b, bt in bank.items():
            for op in OPS:
                if pkey(poly_op(op, dict(a), dict(b))) == ts:
                    return {'cost': 1, 'expression': [op, at, bt]}
    return {'cost': None, 'status': 'not_found_within_1_polynomial_operation'}


def recover_two(tree, wanted):
    first = recover_one(tree, wanted)
    if first['cost'] is not None:
        return first
    target_key = pkey(polynomial(wanted))
    leaves = atoms(tree)
    one = {}
    for a, at in leaves.items():
        for b, bt in leaves.items():
            for op in OPS:
                try:
                    p = pkey(poly_op(op, dict(a), dict(b)))
                except ValueError:
                    return {'cost': None, 'status': 'term_limit'}
                one.setdefault(p, [op, at, bt])
    for a, at in one.items():
        for b, bt in leaves.items():
            for op in OPS:
                for left, right, lt, rt in ((a,b,at,bt),(b,a,bt,at)):
                    try:
                        p = pkey(poly_op(op,dict(left),dict(right)))
                    except ValueError:
                        return {'cost': None, 'status': 'term_limit'}
                    if p == target_key:
                        return {'cost': 2, 'expression': [op,lt,rt]}
    return {'cost': None, 'status': 'not_found_within_2_polynomial_operations'}


def evaluate(tree, env):
    if isinstance(tree, int):
        return tree & MASK
    if isinstance(tree, str):
        return env[tree] & MASK
    op, a, b = tree
    x, y = evaluate(a, env), evaluate(b, env)
    return {'add': lambda: x+y, 'sub': lambda: x-y, 'mul': lambda: x*y}[op]() & MASK
