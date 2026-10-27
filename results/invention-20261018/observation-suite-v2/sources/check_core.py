"""Executable audit of the exact polynomial component; no Wasm claim."""
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys
import core

out = Path(sys.argv[1])
if out.exists():
    raise SystemExit('Refuse overwrite')
out.mkdir(parents=True)
source = ['mul', ['add', ['mul','x','y'], ['mul','z','x']],
          ['add', ['mul','y','z'], 1]]
plan = {'source': source, 'candidate_limit': 96, 'rewrite_depth': 3,
        'target_rule': 'largest proper subtree cost>=2; lexicographic tie break',
        'seed': 20261018, 'scope': 'Exact i32 polynomial core; no binary transformation yet'}
(out/'plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
wanted = core.target(source)  # before generation
pool, stats = core.generate(source)
kept = core.frontier(pool)
profiles = [core.profile(t) for t in kept]
coverage = all(any(core.dominates(q, core.profile(t)) for q in profiles) for t in pool)
if not coverage:
    raise AssertionError('Frontier lost a candidate without dominance witness')
rng = random.Random(plan['seed'])
boundary = (0,1,2,0x7fffffff,0x80000000,0xffffffff)
inputs = list(itertools.product(boundary, repeat=3)) + [tuple(rng.getrandbits(32) for _ in range(3)) for _ in range(512)]
mismatches = []
for t in pool:
    for row in inputs:
        env = dict(zip(('x','y','z'), row))
        if core.evaluate(t,env) != core.evaluate(source,env):
            mismatches.append({'tree':t,'input':row})
# This is a finite implementation check, supplementary to coefficient equality.
target_profiles = [{'tree':t, 'cost':core.cost(t), 'recovery':core.recover_one(t,wanted),
                    'recovery_two':core.recover_two(t,wanted)} for t in kept]
result = {'plan':plan,'stats':stats,'target':wanted,'frontier_size':len(kept),
          'dominance_coverage':coverage,'comparisons':len(pool)*len(inputs),
          'mismatches':mismatches,'frontier':target_profiles,
          'limitations':['One source expression; no Wasm execution or whole-program transformation.',
                         'Recovery limited to 0/1/2 add/sub/mul, not the complete machine-operation or adaptive suite.',
                         'Term rewriting and Pareto filtering are established general techniques.',
                         'No security or novelty conclusion from this component check.'],
          'sourceSHA256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), Path(core.__file__))}}
(out/'pool.json').write_text(json.dumps(pool),encoding='utf-8')
(out/'inputs.json').write_text(json.dumps(inputs),encoding='utf-8')
(out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ('stats','frontier_size','dominance_coverage','comparisons','mismatches')},indent=2))
if mismatches:
    raise SystemExit(1)
