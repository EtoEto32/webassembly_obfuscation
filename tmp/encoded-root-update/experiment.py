import hashlib
import json
import platform
import random
from pathlib import Path
from observer import recover

ROOT = Path(__file__).resolve().parent
SEED = 0x524F4F54


def encode(x, width):
    return (x + 2*x*x) % (1 << width)


def source_step(x, u, width):
    if x % 2:
        return (x + u*u + u) % (1 << width)
    return (x + u*u + u + u + u) % (1 << width)


def encoded_step(z, u, width):
    r = 1
    target = 1 + (z << 3)
    for k in range(2, width):
        correction = ((target - r*r) >> (k+1)) & 1
        r |= correction << k
    mask = (1 << width)-1
    v = (u*u + (u if z & 1 else 3*u)) & mask
    result = (z + v*r + 2*v*v) & mask
    return result, r


def main():
    if (ROOT / 'results.json').exists():
        raise RuntimeError('Preserve previous results; run in a fresh directory.')
    rows = []
    for width in range(3, 9):
        checks = wrong = recovered = root_wrong = 0
        for x in range(1 << width):
            z = encode(x, width)
            for u in range(1 << width):
                candidate, root = encoded_step(z, u, width)
                wrong += candidate != encode(source_step(x, u, width), width)
                recovered += recover(width, z, root) == x
                root_wrong += root != (1+4*x) % (1 << width)
                checks += 1
        rows.append(dict(width=width, checks=checks, output_mismatches=wrong,
                         recovered=recovered, root_mismatches=root_wrong))

    rng = random.Random(SEED)
    boundary = [0,1,2,3,0x3fffffff,0x40000000,0x7fffffff,
                0x80000000,0xfffffffe,0xffffffff]
    cases = [(x, [u]*8) for x in boundary for u in boundary]
    cases += [(rng.getrandbits(32), [rng.getrandbits(32) for _ in range(8)])
              for _ in range(1024)]
    inputs = json.dumps(cases, separators=(',', ':')).encode()
    (ROOT / 'inputs.json').write_bytes(inputs)
    observations = []
    mismatches = recovered = checks = branch_odd = 0
    for case, (initial, stream) in enumerate(cases):
        x, z = initial, encode(initial, 32)
        for step, u in enumerate(stream):
            new_z, root = encoded_step(z, u, 32)
            found = recover(32, z, root)
            recovered += found == x
            branch_odd += x & 1
            new_x = source_step(x, u, 32)
            mismatches += new_z != encode(new_x, 32)
            observations.append(dict(case=case, step=step, z=z, root=root,
                                     recovered=found))
            checks += 1
            x, z = new_x, new_z
    trace_bytes = json.dumps(observations, separators=(',', ':')).encode()
    (ROOT / 'observations.json').write_bytes(trace_bytes)
    result = dict(seed=SEED, python=platform.python_version(), small=rows,
                  i32=dict(cases=len(cases), steps=checks, output_mismatches=mismatches,
                           recovered=recovered, odd_branch_steps=branch_odd),
                  inputs_sha256=hashlib.sha256(inputs).hexdigest(),
                  observations_sha256=hashlib.sha256(trace_bytes).hexdigest(),
                  scripts={f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
                           for f in ['experiment.py', 'observer.py', 'protocol.md']})
    (ROOT / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    assert mismatches == 0 and recovered == checks
    assert all(r['output_mismatches'] == 0 and r['root_mismatches'] == 0
               and r['recovered'] == r['checks'] for r in rows)


if __name__ == '__main__':
    main()
