import hashlib
import json
import platform
from pathlib import Path
from coefficient_observer import recover

ROOT = Path(__file__).resolve().parent

def canonical(poly, modulus):
    return {key: value % modulus for key, value in poly.items() if value % modulus}

def main():
    target = ROOT / 'coefficient-results.json'
    if target.exists():
        raise RuntimeError('Preserve existing results')
    observations = json.loads((ROOT / 'observations.json').read_text())
    originals = json.loads((ROOT / 'results.json').read_text())['factorization']
    assert len(observations) == len(originals) == 8
    rows = []
    for payload, original in zip(observations, originals):
        found = recover(payload)
        c = original['source_coefficients']
        m = 1 << payload['width']
        expected = [canonical({(2,0):1, (1,1):c[0], (0,1):c[1]}, m),
                    canonical({(0,2):1, (1,0):c[2], (1,1):c[3]}, m)]
        matches = [a == b for a, b in zip(found, expected)]
        mutant = dict(found[0])
        mutant[(0,0)] = (mutant.get((0,0), 0) + 1) % m
        rejected = canonical(mutant, m) != expected[0]
        assert all(matches) and rejected
        rows.append(dict(group=original['group'], instance=original['instance'],
                         recovered=[[[list(k),v] for k,v in sorted(p.items())] for p in found],
                         exact_matches=matches, mutant_rejected=rejected))
    names = ['coefficient_observer.py', 'check_coefficients.py',
             'coefficient-protocol.md', 'observations.json', 'results.json']
    result = dict(python=platform.python_version(), cases=rows,
                  hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names})
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(cases=len(rows), exact_relations=sum(sum(r['exact_matches']) for r in rows),
                         mutants_rejected=sum(r['mutant_rejected'] for r in rows))))

if __name__ == '__main__':
    main()
