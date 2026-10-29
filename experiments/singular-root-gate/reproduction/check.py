import hashlib
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def ev(c, x, y, m):
    return (c[0] + c[1]*x + c[2]*y + c[3]*x*y + c[4]*x*x + c[5]*y*y) % m


def jac(c, x, y):
    return ((c[1] + c[3]*y + 2*c[4]*x) & 1,
            (c[2] + c[3]*x + 2*c[5]*y) & 1)


def kernel(rows):
    return [(u, v) for u, v in itertools.product(range(2), repeat=2)
            if all((a*u + b*v) % 2 == 0 for a, b in rows)]


def main():
    out = ROOT / "results.json"
    if out.exists(): raise FileExistsError(out)
    coeffs = [tuple(c) + (0, 0) for c in itertools.product(range(4), repeat=4)]
    points = list(itertools.product(range(4), repeat=2))
    masks = [sum((ev(c, x, y, 4) == 0) << i for i, (x, y) in enumerate(points)) for c in coeffs]
    histogram, unique, singular, verified, witnesses = {}, 0, 0, 0, []
    classifications = []
    for i, c in enumerate(coeffs):
        for j, d in enumerate(coeffs):
            roots = masks[i] & masks[j]
            count = roots.bit_count()
            histogram[count] = histogram.get(count, 0) + 1
            if count == 1: unique += 1
            classifications.append([i, j, roots])
            for bit, (x, y) in enumerate(points):
                if not (roots >> bit) & 1: continue
                rows = [jac(c, x, y), jac(d, x, y)]
                k = kernel(rows)
                if len(k) > 1: singular += 1
                if count == 1: assert len(k) == 1
                for u, v in k:
                    z, t = (x + 2*u) % 4, (y + 2*v) % 4
                    assert ev(c, z, t, 4) == ev(d, z, t, 4) == 0
                    verified += 1
                if len(k) > 1 and len(witnesses) < 8:
                    witnesses.append({"coefficients": [c, d], "root": [x, y], "jacobian": rows,
                                      "kernel": k, "top_bit_roots": [[(x+2*u)%4, (y+2*v)%4] for u,v in k]})
    rng = random.Random(271009)
    wide = []
    modulus = 1 << 32
    for _ in range(256):
        x, y = rng.randrange(modulus), rng.randrange(modulus)
        polynomials = []
        for _ in range(2):
            c = [0] + [rng.randrange(modulus) for _ in range(5)]
            c[0] = -ev(c, x, y, modulus) % modulus
            polynomials.append(c)
        rows = [jac(c, x, y) for c in polynomials]
        k = kernel(rows)
        shifts = []
        for u, v in itertools.product(range(2), repeat=2):
            z, t = (x + (u << 31)) % modulus, (y + (v << 31)) % modulus
            values = [ev(c, z, t, modulus) for c in polynomials]
            assert (values == [0, 0]) == ((u, v) in k)
            shifts.append({"delta": [u, v], "point": [z, t], "values": values})
        wide.append({"coefficients": polynomials, "root": [x, y], "jacobian": rows,
                     "kernel_size": len(k), "perturbations": shifts})
    # Boundaries of the theorem, not secure alternative constructions.
    assert [x for x in range(2) if x*x % 2 == 0] == [0]
    assert 2*0 % 2 == 0
    rol4 = lambda x: ((x << 1) | (x >> 3)) & 15
    assert rol4(8) - rol4(0) == 1
    report = {"systems": len(classifications), "root_count_histogram": histogram,
              "unique_root_systems": unique, "unique_singular_root_systems": 0,
              "singular_root_occurrences": singular, "kernel_shift_checks": verified,
              "witnesses": witnesses, "wide_cases": wide,
              "controls": {"w1_square_unique_root": 0, "w1_derivative_at_root": 0,
                           "rotation4_top_bit_difference": 1},
              "hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ["check.py", "protocol.json"]}}
    (ROOT / "classifications.json").write_text(json.dumps({"coefficients": coeffs, "systems": classifications}, indent=2) + "\n")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("witnesses", "wide_cases", "hashes")}, indent=2))


if __name__ == "__main__": main()
