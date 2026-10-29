"""Exact finite utility check of the observation frontier, without new obfuscation claims."""
from collections import Counter
from functools import lru_cache
import importlib.util
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'original_frontier.py'
spec = importlib.util.spec_from_file_location('frontier_source', SOURCE)
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
            pivot = v.bit_length() - 1
            if pivot not in b:
                b[pivot] = v
                break
            v ^= b[pivot]
    return tuple(b[p] for p in sorted(b, reverse=True))

def member(v, bs):
    for w in bs:
        if v and v.bit_length() == w.bit_length():
            v ^= w
    return not v

@lru_cache(None)
def space(seen, degree):
    atoms = basis(bits(base + list(seen)))
    current = atoms
    for _ in range(1, degree):
        current = basis(current + tuple(x & y for x in current for y in atoms))
    return current

def dominates(p, q):
    return p.sig == q.sig and p.cost <= q.cost and all(member(v, space(q.seen, 1)) for v in space(p.seen, 1))

if (ROOT / 'results.json').exists():
    raise SystemExit('Refusing overwrite')
all_bank, all_stats = m.generate('all_profiles')
single, single_stats = m.generate('output_only')
m.dominates = dominates
frontier, frontier_stats = m.generate('frontier')
summary = {}
examples = []
source_target_audit = []
for label, bank in [('all_profiles', all_bank), ('span_frontier', frontier)]:
    summary[label] = {}
    for degree in (1, 2, 3, 4):
        counts = Counter()
        for sig, terms in bank.items():
            default = single[sig][0]
            old = space(default.seen, degree)
            for t in terms:
                new = space(t.seen, degree)
                a = all(member(v, old) for v in new)
                b = all(member(v, new) for v in old)
                relation = 'equal' if a and b else 'strict_subset' if a else 'strict_superset' if b else 'incomparable'
                counts[relation] += 1
                if relation == 'strict_subset':
                    counts['strict_subset_same_cost' if t.cost == default.cost else 'strict_subset_extra_cost'] += 1
                    if label == 'span_frontier' and degree == 2:
                        missing = []
                        for observed in default.seen - {sig}:
                            for bit, value in enumerate(bits([observed])):
                                if not member(value, new):
                                    missing.append(dict(bit=bit, target_truth_table=value, word_signature=observed))
                        source_target_audit.append(dict(candidate=t.tree, baseline=default.tree,
                            candidate_cost=t.cost, baseline_cost=default.cost,
                            unrecovered_baseline_intermediate_bits=missing))
                if degree == 2 and relation in ('strict_subset', 'incomparable') and len(examples) < 8:
                    witness = next(v for v in old if not member(v, new))
                    examples.append(dict(bank=label, candidate=t.tree, baseline=default.tree,
                        candidate_cost=t.cost, baseline_cost=default.cost, relation=relation,
                        candidate_rank=len(new), baseline_rank=len(old), target_truth_table=witness))
        summary[label][str(degree)] = dict(counts)

# Independently characterize second-degree closure by enumerating all products
# of original bit observations; compare to products of the reduced linear basis.
independent_checks = 0
for terms in all_bank.values():
    for t in terms:
        original = bits(base + list(t.seen))
        direct = basis(original + tuple(x & y for x in original for y in original))
        reduced = space(t.seen, 2)
        assert len(direct) == len(reduced)
        assert all(member(v, direct) for v in reduced)
        independent_checks += 1
result = dict(domain='all 16 assignments of two 2-bit inputs', grammar='add/sub/xor/mul, constants 0/1, <=3 expression-tree operations',
    stats=dict(all_profiles=all_stats, output_only=single_stats, span_frontier=frontier_stats),
    comparisons=summary, second_degree_examples=examples, direct_product_checks=independent_checks)
result['source_target_audit'] = source_target_audit
result['rank_improvements_with_any_unrecovered_source_intermediate'] = sum(bool(x['unrecovered_baseline_intermediate_bits']) for x in source_target_audit)
(ROOT / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
