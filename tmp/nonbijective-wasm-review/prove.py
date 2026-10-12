"""Prove the six residual-precision steps for all i32 residuals."""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/'.tools/encoding-synthesis-python'))
import z3

a, b = z3.BitVecs('a b', 32)
na, nb = -a*(a+1)*b, -b*(b+1)*a
rows = []
for k, target in [(0,1),(1,2),(2,4),(4,8),(8,16),(16,32)]:
    s = z3.Solver()
    s.set(timeout=10000)
    s.add(a & ((1<<k)-1) == 0, b & ((1<<k)-1) == 0)
    mask = (1<<target)-1
    s.add(z3.Or(na & mask != 0, nb & mask != 0))
    verdict = str(s.check())
    rows.append({'inputPrecision':k,'outputPrecision':target,'counterexample':verdict})
    if verdict != 'unsat':
        raise RuntimeError(rows)
out = {'z3':z3.get_version_string(),'lemmas':rows,
       'scope':'Residual update only; WAT generation and execution checked separately.'}
(HERE/'proof.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
