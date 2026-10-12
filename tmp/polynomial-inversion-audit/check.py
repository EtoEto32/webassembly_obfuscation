import hashlib
import json
import platform
import random
from pathlib import Path
from recover import recover, evaluate

ROOT = Path(__file__).resolve().parent
SEED = 0x504F4C59


def polynomial(coefficients, x, modulus):
    # Reference evaluator uses explicit powers, not the model's Newton basis.
    return sum(c * pow(x, i, modulus) for i,c in enumerate(coefficients)) % modulus


def main():
    if (ROOT / 'results.json').exists():
        raise RuntimeError('Do not overwrite prior experiment.')
    rng = random.Random(SEED)
    cases, rows, models = [], [], []
    for width in [3,4,5,6,7,8,16,32,64]:
        modulus = 1 << width
        for degree in [1,2,3,7,17,65]:
            for instance in range(3):
                coeff = [rng.randrange(modulus) for _ in range(degree+1)]
                coeff[1] |= 1
                if degree >= 2:
                    coeff[2] ^= sum(coeff[2::2]) & 1
                if degree >= 3:
                    coeff[3] ^= sum(coeff[3::2]) & 1
                calls = 0
                def oracle(x):
                    nonlocal calls
                    calls += 1
                    return polynomial(coeff, x, modulus)
                model = recover(width, oracle)
                inputs = list(range(modulus)) if width <= 8 else list(dict.fromkeys(
                    [0,1,2,3,modulus//2-1,modulus//2,modulus-2,modulus-1] +
                    [rng.randrange(modulus) for _ in range(1024)]))
                failures = []
                for x in inputs:
                    y = polynomial(coeff, x, modulus)
                    actual = evaluate(model, y)
                    if actual != x:
                        failures.append(dict(x=x, y=y, recovered=actual))
                ident = len(cases)
                cases.append(dict(id=ident, width=width, degree_bound=degree,
                                  coefficients=coeff, inputs=inputs))
                models.append(dict(id=ident, **model))
                rows.append(dict(id=ident, width=width, degree_bound=degree,
                                 oracle_calls=calls, checks=len(inputs),
                                 failures=failures))
    for name, data in [('inputs.json',cases), ('models.json',models)]:
        (ROOT/name).write_text(json.dumps(data, separators=(',',':')), encoding='utf-8')
    result = dict(seed=SEED, python=platform.python_version(), cases=len(rows),
                  checks=sum(r['checks'] for r in rows),
                  failures=sum(len(r['failures']) for r in rows), rows=rows,
                  hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
                          for f in ['inputs.json','models.json','recover.py','check.py','protocol.md']})
    (ROOT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['seed','python','cases','checks','failures']}))
    print(json.dumps({str(w):sorted(set(r['oracle_calls'] for r in rows if r['width']==w))
                      for w in sorted(set(r['width'] for r in rows))}))
    assert result['failures'] == 0


if __name__ == '__main__':
    main()
