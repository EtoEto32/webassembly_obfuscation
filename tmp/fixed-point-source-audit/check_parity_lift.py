"""Independent Boolean evaluator checks the parity projection at every step."""
import hashlib
import json
import random
from pathlib import Path
import check_bitlift as circuit

here = Path(__file__).resolve().parent
out = here / 'parity-lift-results.json'
if out.exists():
    raise FileExistsError(out)
rng = random.Random(2026101204)
rows = []
for width in [2, 8, 32]:
    mask = (1 << width)-1
    for trial in range(5):
        words = [rng.getrandbits(32) for _ in range(3)]
        ext = circuit.inputs(words)
        v = [rng.getrandbits(width) for _ in range(circuit.N)]
        boolean = [x & 1 for x in v]
        for step in range(1, circuit.DEPTH+1):
            values = ext + v
            f = [circuit.polynomial(op, values[a], values[b]) & mask
                 for op, a, b in circuit.gates]
            residual = [(a-b) & mask for a, b in zip(v, f)]
            v = [(f[i]-2*(residual[i]+residual[(i+1) % circuit.N])) & mask
                 for i in range(circuit.N)]
            old = ext + boolean
            boolean = [(old[a] ^ old[b]) if op == 'xor' else
                       (old[a] & old[b]) if op == 'and' else
                       (old[a] | old[b]) for op, a, b in circuit.gates]
            assert [x & 1 for x in v] == boolean
        assert circuit.extract(boolean) == circuit.t2(*words)
        rows.append(dict(width=width, trial=trial, input=words,
                         output=circuit.extract(boolean),
                         nonzero_upper_coordinates=sum(x > 1 for x in v)))
assert any(r['nonzero_upper_coordinates'] for r in rows)
report = dict(scope='Parity semiconjugacy of local T2; not a full hash',
              cases=len(rows), steps_per_case=circuit.DEPTH,
              coordinate_comparisons=len(rows)*circuit.DEPTH*circuit.N,
              mismatches=0, seed=2026101204,
              sha256={name:hashlib.sha256((here/name).read_bytes()).hexdigest()
                      for name in ['check_parity_lift.py', 'check_bitlift.py']},
              results=rows)
out.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'results'}))
