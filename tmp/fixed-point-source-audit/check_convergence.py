import hashlib
import itertools
import json
import platform
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run_case(w, x, initial):
    mask = (1 << w)-1
    root = [x, (x*x+1)&mask]
    v = list(initial)
    trace = [v[:]]
    for step in range(1, 2*w+1):
        f = [x, (v[0]*v[0]+1)&mask]
        residual = [a-b for a,b in zip(v,f)]
        v = [(f[0]-2*(residual[0]+residual[1]))&mask,
             (f[1]-2*residual[0])&mask]
        if step % 2 == 0:
            precision = 1 << (step//2)
            assert all((a-b)%precision == 0 for a,b in zip(v,root))
        trace.append(v[:])
    assert v == root
    return trace

def main():
    output = ROOT/'convergence-results.json'
    if output.exists():
        raise FileExistsError(output)
    rows = []
    for w in range(1,5):
        count = 0
        for x,a,b in itertools.product(range(1 << w), repeat=3):
            run_case(w,x,(a,b))
            count += 1
        rows.append(dict(width=w,cases=count,milestones=count*w))
    rng = random.Random(20261012)
    examples = []
    for i in range(64):
        x,a,b = [rng.getrandbits(32) for _ in range(3)]
        trace = run_case(32,x,(a,b))
        examples.append(dict(x=x,initial=[a,b],final=trace[-1],trace=trace if i==0 else None))
    cycle = [[2,0]]
    for _ in range(3):
        a,b = cycle[-1]
        cycle.append([(-2*(b-(a>>1)))&3, a>>1])
    assert cycle == [[2,0],[2,1],[0,1],[2,0]]
    assert all(v != [0,0] for v in cycle)
    result = dict(python=platform.python_version(), exhaustive=rows,
                  seed=20261012, word32=examples, excluded_cycle=cycle,
                  sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                          for name in ['check_convergence.py','convergence.md']})
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(exhaustive_cases=sum(r['cases'] for r in rows),
                          word32_cases=len(examples),excluded_cycle=cycle)))

if __name__ == '__main__':
    main()
