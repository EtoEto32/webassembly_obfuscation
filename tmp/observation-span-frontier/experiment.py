"""Compare exact observation sets with GF(2) span dominance in a finite grammar."""
import functools
import importlib.util
import itertools
import json
from pathlib import Path
import time
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'original_frontier.py'
spec = importlib.util.spec_from_file_location('original_frontier', SOURCE)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
states = list(itertools.product(range(4), repeat=2))
base = [tuple(s[i] for s in states) for i in range(2)] + [tuple([1]*16)]

def bits(signatures):
    return tuple(sum(((v >> bit) & 1) << i for i, v in enumerate(sig))
                 for sig in signatures for bit in range(2))

def basis(vectors):
    b = {}
    for v in vectors:
        while v:
            p = v.bit_length() - 1
            if p not in b:
                b[p] = v
                break
            v ^= b[p]
    return tuple(b[p] for p in sorted(b, reverse=True))

@functools.lru_cache(None)
def space(seen):
    return basis(bits(base + list(sorted(seen))))

def included(p, q):
    for v in p:
        for w in q:
            if v and v.bit_length() == w.bit_length():
                v ^= w
        if v:
            return False
    return True

def dominates(p, q):
    return p.sig == q.sig and p.cost <= q.cost and included(space(p.seen), space(q.seen))

def closure(vectors):
    # Independent subset-XOR construction, no Gaussian elimination.
    out = {0}
    for v in vectors:
        out |= {x ^ v for x in out}
    return out

if (ROOT / 'results.json').exists():
    raise SystemExit('Refusing to overwrite')
banks, stats = {}, {}
for name, mode in [('baseline', 'all_profiles'), ('set_frontier', 'frontier'), ('output_only', 'output_only'), ('span_frontier', 'frontier')]:
    if name == 'span_frontier':
        m.dominates = dominates
    start = time.perf_counter()
    banks[name], stats[name] = m.generate(mode)
    stats[name]['seconds'] = time.perf_counter() - start
    print(name, stats[name], flush=True)

checked = 0
missing_output = []
strict_examples = []
for sig, terms in banks['baseline'].items():
    for t in terms:
        choices = [p for p in banks['span_frontier'][sig] if dominates(p, t)]
        assert choices
        p = choices[0]
        assert closure(bits(base + list(p.seen))) <= closure(bits(base + list(t.seen)))
        checked += 1
        if not p.seen <= t.seen and len(strict_examples) < 6:
            strict_examples.append(dict(kept=p.tree, replaced=t.tree, kept_cost=p.cost, replaced_cost=t.cost,
                                       kept_rank=len(space(p.seen)), replaced_rank=len(space(t.seen))))
        if not any(dominates(p, t) for p in banks['output_only'][sig]) and len(missing_output) < 6:
            missing_output.append(dict(lost=t.tree, kept=banks['output_only'][sig][0].tree))

# Every one-step pure context adds identical observations for same output.
# Check all binary ops/operands on retained pairs used above, using bitwise products
# of basis functions as degree-two decoder features.
context_checks = 0
for sig, terms in banks['baseline'].items():
    for t in terms:
        p = next(p for p in banks['span_frontier'][sig] if dominates(p, t))
        for other in base:
            for op in m.OPS:
                out = tuple(m.apply(op, x, y, 3) for x, y in zip(sig, other))
                ps = space(p.seen | {out})
                qs = space(t.seen | {out})
                pd = basis(ps + tuple(x & y for x in ps for y in ps))
                qd = basis(qs + tuple(x & y for x in qs for y in qs))
                assert included(pd, qd)
                context_checks += 1
result = dict(grammar='two 2-bit inputs; constants 0,1; add/sub/xor/mul; pure expression trees <=3 operations',
              observer='all bits of inputs/constants/intermediates; polynomial decoder degree bounded, unlimited XOR terms',
              stats=stats, coverage_checks=checked, coverage_failures=0, contextual_degree2_checks=context_checks,
              strict_span_examples=strict_examples, output_only_missing_examples=missing_output)
(ROOT / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print('coverage', checked, 'contexts', context_checks, 'strict examples', len(strict_examples), flush=True)
