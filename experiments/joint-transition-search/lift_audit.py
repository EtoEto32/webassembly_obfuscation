"""Audit explicit lifts of previously generated finite-state correspondences."""
import hashlib
import itertools
import json
import platform
import random
from pathlib import Path
from search import primitive

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "lift-artifacts"


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def encode(x, y, w, fit, signed):
    m = (1 << w) - 1
    c = fit["c"][y & 7]
    off = fit["offset"]
    if signed:
        c = (c + 4) % 8 - 4
        off = (off + 4) % 8 - 4
    a, b = (fit["sign"] * x + c) & m, (y + off) & m
    if fit["swap"]:
        a, b = b, a
    return a | (b << w)


def main():
    OUT.mkdir(exist_ok=False)
    protocol = json.loads((ROOT / "lift-protocol.json").read_text())
    solutions = json.loads((ROOT / "artifacts/solutions.json").read_text())
    catalog = json.loads((ROOT / "artifacts/catalog.json").read_text())
    rng = random.Random(protocol["seed"])
    n = 1 << 32
    boundary = [0, 1, 2, 7, 8, n // 2, n - 2, n - 1]
    inputs = {4: list(itertools.product(range(16), repeat=2)),
              32: list(itertools.product(boundary, repeat=2)) +
                  [(rng.randrange(n), rng.randrange(n)) for _ in range(256)]}
    write("inputs.json", inputs)
    fits, summaries = [], []
    for idx, solution in enumerate(solutions):
        table = solution["encoding"]
        matches = []
        for swap, sign, offset in itertools.product([False, True], [1, -1], range(8)):
            c = [((table[y << 3] >> 3) if swap else table[y << 3]) & 7 for y in range(8)]
            fit = {"swap": swap, "sign": sign, "offset": offset, "c": c}
            if all(encode(x, y, 3, fit, False) == table[x | (y << 3)]
                   for x, y in itertools.product(range(8), repeat=2)):
                matches.append(fit)
        assert len(matches) == 1, (idx, len(matches))
        fit = matches[0]
        fits.append({"solution": idx, "fit": fit})
        programs = [catalog[i]["program"] for i in solution["updates"]]
        for signed in [False, True]:
            for w, points in inputs.items():
                m = (1 << w) - 1
                rows = []
                for x, y in points:
                    plain_next = [((x + y) & m, y),
                                  (x ^ (((y << 1) | (y >> (w - 1))) & m), (y + 1) & m)]
                    for label, (nx, ny) in enumerate(plain_next):
                        current = encode(x, y, w, fit, signed)
                        actual = current
                        for op in programs[label]:
                            actual = primitive(op, actual, w)
                        expected = encode(nx, ny, w, fit, signed)
                        rows.append({"x": x, "y": y, "label": label, "encoded": current,
                                     "expected": expected, "actual": actual})
                failures = [r for r in rows if r["actual"] != r["expected"]]
                name = f"solution{idx}-{'signed' if signed else 'unsigned'}-w{w}.json"
                write(name, rows)
                summaries.append({"solution": idx, "signed": signed, "width": w,
                                  "checks": len(rows), "failures": len(failures),
                                  "first_counterexample": failures[0] if failures else None,
                                  "rows_file": name})
    write("fits.json", fits)
    write("cases.json", summaries)
    result = {"python": platform.python_version(), "fitted_solutions": len(fits),
              "aggregate": [{"width": w, "signed": signed,
                             "variants": len([r for r in summaries if r["width"] == w and r["signed"] == signed]),
                             "passing": sum(r["failures"] == 0 for r in summaries if r["width"] == w and r["signed"] == signed),
                             "checks": sum(r["checks"] for r in summaries if r["width"] == w and r["signed"] == signed)}
                            for w, signed in itertools.product(inputs, [False, True])],
              "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                for name in ["lift_audit.py", "lift-protocol.json", "search.py",
                                             "artifacts/solutions.json", "artifacts/catalog.json"]}}
    write("results.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
