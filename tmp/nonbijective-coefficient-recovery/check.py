import hashlib
import json
from pathlib import Path
import platform
import random
import sys
from observer import recover

ROOT = Path(__file__).resolve().parent
SEED = 0x434F4546

def evaluate(poly, x, y, modulus):
    return sum(c * pow(x, i, modulus) * pow(y, j, modulus)
               for (i, j), c in poly.items()) % modulus

def main():
    source = Path(sys.argv[1])
    destination = ROOT / 'results.json'
    if destination.exists():
        raise RuntimeError('Preserve existing results; use a fresh directory')
    observations = json.loads((source / 'observations.json').read_text())
    prior = json.loads((source / 'results.json').read_text())['factorization']
    if len(observations) != len(prior):
        raise ValueError('Mismatched case counts')
    rng = random.Random(SEED)
    rows = []
    for payload, expected in zip(observations, prior):
        f, g = recover(payload)
        c = expected['source_coefficients']  # Verifier only, never passed to observer.
        modulus = 1 << payload['width']
        wanted = [{(2, 0): 1, (1, 1): c[0], (0, 1): c[1]},
                  {(0, 2): 1, (1, 0): c[2], (1, 1): c[3]}]
        wanted = [{k: v % modulus for k, v in p.items() if v % modulus} for p in wanted]
        exact = [f == wanted[0], g == wanted[1]]
        boundary = [0, 1, 2, (modulus // 2)-1, modulus // 2, modulus-2, modulus-1]
        inputs = [(x, y) for x in boundary for y in boundary]
        inputs += [(rng.randrange(modulus), rng.randrange(modulus)) for _ in range(2048)]
        mismatches = 0
        for x, y in inputs:
            observed = evaluate(f, x, y, modulus), evaluate(g, x, y, modulus)
            reference = ((x*x+c[0]*x*y+c[1]*y) % modulus,
                         (y*y+c[2]*x+c[3]*x*y) % modulus)
            mismatches += observed != reference
        rows.append(dict(group=expected['group'], instance=expected['instance'],
                         exact_coefficients=exact, input_pairs=len(inputs), mismatches=mismatches,
                         recovered=[[[list(k), v] for k, v in sorted(p.items())] for p in [f, g]]))
    result = dict(python=platform.python_version(), seed=SEED, cases=rows,
                  source_hashes={name: hashlib.sha256((source/name).read_bytes()).hexdigest()
                                 for name in ['observations.json', 'results.json']},
                  code_hashes={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                               for name in ['observer.py', 'check.py']})
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(cases=len(rows), exact_recovered=sum(all(r['exact_coefficients']) for r in rows),
                         input_pairs=sum(r['input_pairs'] for r in rows),
                         mismatches=sum(r['mismatches'] for r in rows))))
    assert all(all(r['exact_coefficients']) and r['mismatches']==0 for r in rows)

if __name__ == '__main__':
    main()
