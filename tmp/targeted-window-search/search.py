"""Exact small-width window search with predeclared logical targets."""
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import itertools
import json
import time

ROOT = Path(__file__).resolve().parent
WIDTH, MASK = 3, 7
STATES = list(itertools.product(range(8), repeat=2))
OPS = ('add', 'sub', 'xor', 'mul')

def calc(op, x, y):
    if op == 'add': return (x+y)&MASK
    if op == 'sub': return (x-y)&MASK
    if op == 'mul': return (x*y)&MASK
    if op == 'xor': return x^y
    if op == 'and': return x&y
    if op == 'or': return x|y
    raise ValueError(op)

LEAVES = {name: tuple(fn(*s) for s in STATES) for name, fn in (
    ('a', lambda a,b:a), ('b', lambda a,b:b), ('zero', lambda a,b:0), ('one', lambda a,b:1))}

def evaluate(tree):
    if isinstance(tree, str): return LEAVES[tree]
    op, left, right = tree
    return tuple(calc(op,x,y) for x,y in zip(evaluate(left), evaluate(right)))

# Chosen before generating candidates. Each target is an actual source intermediate.
# These are synthetic arithmetic kernels, not indispensable real-world secrets.
TARGETS = [
    ('xor_product_sum', ['xor', ['mul','a','b'], ['add','a','b']], 'b'),
    ('difference_of_squares', ['mul', ['sub','a','b'], ['add','a','b']], 'a'),
    ('xor_two_products', ['xor', ['mul','a','b'], ['mul','a','a']], 'b'),
]

@dataclass
class Term:
    sig: tuple
    seen: frozenset
    cost: int
    tree: object

def generate():
    levels = [[Term(sig, frozenset(), 0, name) for name,sig in LEAVES.items()]]
    groups = {t.sig: {t.seen:t} for t in levels[0]}
    stats = []
    for cost in range(1,5):
        added, attempts = [], 0
        for lc in range(cost):
            for p in levels[lc]:
                for q in levels[cost-1-lc]:
                    for op in OPS:
                        attempts += 1
                        sig = tuple(calc(op,x,y) for x,y in zip(p.sig,q.sig))
                        seen = p.seen | q.seen | ({sig} if sig not in LEAVES.values() else set())
                        seen = frozenset(seen)
                        bank = groups.setdefault(sig,{})
                        if seen in bank: continue
                        t = Term(sig,seen,cost,[op,p.tree,q.tree])
                        bank[seen] = t
                        added.append(t)
        levels.append(added)
        stats.append(dict(cost=cost, attempts=attempts, retained=len(added)))
        print(stats[-1],flush=True)
    return groups, stats

def basis(vectors):
    b={}
    for v in vectors:
        while v:
            p=v.bit_length()-1
            if p not in b:
                b[p]=v
                break
            v ^= b[p]
    return tuple(b[p] for p in sorted(b,reverse=True))

def bits(sig):
    return tuple(sum(((v>>j)&1)<<i for i,v in enumerate(sig)) for j in range(WIDTH))

def member(v,bs):
    for w in bs:
        if v and v.bit_length()==w.bit_length(): v ^= w
    return v==0

@lru_cache(None)
def quadratic(seen):
    atoms=basis(tuple(v for sig in tuple(LEAVES.values())+tuple(seen) for v in bits(sig)))
    return basis(atoms+tuple(x&y for x in atoms for y in atoms))

def recover_word(target,seen):
    atoms={sig:f'observed_{i}' for i,sig in enumerate(sorted(seen | frozenset(LEAVES.values())))}
    for k in range(8): atoms[tuple([k]*64)]=f'constant_{k}'
    if target in atoms: return dict(cost=0, expression=atoms[target])
    operators=('add','sub','mul','xor','and','or')
    first={}
    for p,pn in atoms.items():
        for q,qn in atoms.items():
            for op in operators:
                sig=tuple(calc(op,x,y) for x,y in zip(p,q))
                expr=[op,pn,qn]
                if sig==target:return dict(cost=1,expression=expr)
                if sig not in atoms:first.setdefault(sig,expr)
    for p,pn in first.items():
        for q,qn in atoms.items():
            for op in operators:
                for left,right,ln,rn in ((p,q,pn,qn),(q,p,qn,pn)):
                    sig=tuple(calc(op,x,y) for x,y in zip(left,right))
                    if sig==target:return dict(cost=2,expression=[op,ln,rn])
    return None

if (ROOT/'results.json').exists():raise SystemExit('Refuse overwrite')
start=time.perf_counter()
groups,stats=generate()
cases=[]
for name,target,multiplier in TARGETS:
    source=['mul',target,multiplier]
    out,secret=evaluate(source),evaluate(target)
    candidates=list(groups.get(out,{}).values())
    rows=[]
    for t in candidates:
        bs=quadratic(t.seen)
        missing=[j for j,v in enumerate(bits(secret)) if not member(v,bs)]
        if not missing: continue
        recovery=recover_word(secret,t.seen)
        rows.append(dict(tree=t.tree,cost=t.cost,unrecovered_quadratic_bits=missing,
            word_recovery=recovery,observations=[list(x) for x in sorted(t.seen | frozenset(LEAVES.values()))]))
    case=dict(name=name,source=source,target=target,candidate_count=len(candidates),
        all_target_bits_quadratically_recoverable=len(candidates)-len(rows),
        candidate_rows=rows, all_candidates=[dict(tree=t.tree,cost=t.cost,
            target_directly_observed=secret in t.seen,
            signature=t.sig) for t in candidates])
    cases.append(case)
    print(name,'candidates',len(candidates),'quadratic survivors',len(rows),'two-op survivors',sum(x['word_recovery'] is None for x in rows),flush=True)
result=dict(width=WIDTH,states=STATES,operators=OPS,max_tree_ops=4,stats=stats,cases=cases,
    seconds=time.perf_counter()-start)
(ROOT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
