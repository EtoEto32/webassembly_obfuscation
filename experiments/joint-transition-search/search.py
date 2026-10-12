"""Finite update-first representation search with exhaustive certificates."""
import argparse
import hashlib
import itertools
import json
import platform
import random
import subprocess
import sys
import time
from pathlib import Path
from conjugacy import solve

ROOT = Path(__file__).resolve().parent


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def primitive(name, state, w):
    m = (1 << w) - 1
    a, b = state & m, state >> w
    rol = lambda x: ((x << 1) | (x >> (w - 1))) & m
    if name == "inc_a": a += 1
    elif name == "dec_a": a -= 1
    elif name == "inc_b": b += 1
    elif name == "dec_b": b -= 1
    elif name == "add_a_b": a += b
    elif name == "sub_a_b": a -= b
    elif name == "xor_a_b": a ^= b
    elif name == "add_b_a": b += a
    elif name == "sub_b_a": b -= a
    elif name == "xor_b_a": b ^= a
    elif name == "rot_a": a = rol(a)
    elif name == "rot_b": b = rol(b)
    elif name == "swap": a, b = b, a
    elif name == "xor_a_rol_b": a ^= rol(b)
    elif name == "xor_b_rol_a": b ^= rol(a)
    elif name == "mul_a_3": a *= 3
    elif name == "mul_b_3": b *= 3
    else: raise ValueError(name)
    return (a & m) | ((b & m) << w)


def cycle_profile(p):
    remaining, lengths = set(range(len(p))), []
    while remaining:
        x, count = min(remaining), 0
        while x in remaining:
            remaining.remove(x)
            count += 1
            x = p[x]
        lengths.append(count)
    return tuple(sorted(lengths))


def verify(source, target, e):
    return (e is not None and sorted(e) == list(range(len(e)))
            and all(e[s[x]] == t[e[x]]
                    for s, t in zip(source, target) for x in range(len(e))))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts")
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=False)
    protocol = json.loads((ROOT / "protocol.json").read_text())
    start = time.monotonic()
    w = protocol["width"]
    n, mask = 1 << (2 * w), (1 << w) - 1
    states = list(range(n))
    # Direct source specification, separate from primitive dispatch.
    source = [[], []]
    for state in states:
        x, y = state & mask, state >> w
        rotation = ((y * 2) % (mask + 1)) + (y // (1 << (w - 1)))
        source[0].append(((x + y) % (mask + 1)) + (y << w))
        source[1].append((x ^ rotation) + (((y + 1) % (mask + 1)) << w))
    assert solve(source, source, 0) == states
    # Enumerate every grammar sequence, quotient ONLY by its full transition table.
    programs = [()]
    for k in range(1, protocol["maximum_update_length"] + 1):
        programs.extend(itertools.product(protocol["grammar"], repeat=k))
    catalog, seen = [], {}
    for program in programs:
        table = []
        for x in states:
            for op in program:
                x = primitive(op, x, w)
            table.append(x)
        assert sorted(table) == states
        key = tuple(table)
        if key in seen:
            catalog[seen[key]]["aliases"].append(program)
        else:
            seen[key] = len(catalog)
            catalog.append({"program": program, "aliases": [], "table": table,
                            "profile": cycle_profile(table)})
    eligible = [[i for i, c in enumerate(catalog) if c["profile"] == cycle_profile(s)]
                for s in source]
    solutions, pair_records, attempts = [], [], 0
    for left in eligible[0]:
        for right in eligible[1]:
            if time.monotonic() - start > protocol["limits"]["search_seconds"]:
                dump(out / "partial.json", {"error": "timeout", "attempts": attempts})
                raise TimeoutError("finite search did not complete")
            target = [catalog[left]["table"], catalog[right]["table"]]
            roots = []
            for root in states:
                attempts += 1
                e = solve(source, target, root)
                if e is not None:
                    assert verify(source, target, e)
                    roots.append(root)
                    solutions.append({"updates": [left, right], "root": root, "encoding": e,
                                      "encoding_in_update_catalog": seen.get(tuple(e))})
            pair_records.append({"updates": [left, right], "valid_roots": roots})
    # Full tiny-model oracle comparison: all candidate permutation pairs, all roots.
    perms = list(itertools.permutations(range(4)))
    tiny_source = [[1, 2, 3, 0], [1, 0, 3, 2]]
    control_count = 0
    for p, q in itertools.product(perms, repeat=2):
        expected = {e[0]: list(e) for e in perms if verify(tiny_source, [p, q], e)}
        for root in range(4):
            assert solve(tiny_source, [p, q], root) == expected.get(root)
            control_count += 1
    # Arbitrary relabeling checks that the solver did not assume polynomial encodings.
    e = list(states)
    random.Random(69311).shuffle(e)
    arbitrary = [[0] * n for _ in source]
    for i, s in enumerate(source):
        for x in states: arbitrary[i][e[x]] = e[s[x]]
    assert solve(source, arbitrary, e[0]) == e
    mutation = list(e)
    mutation[0], mutation[1] = mutation[1], mutation[0]
    assert not verify(source, arbitrary, mutation)
    dump(out / "controls.json", {"tiny_cases": control_count, "arbitrary_encoding": e,
                                 "arbitrary_target": arbitrary, "mutation_rejected": True})
    # Attack receives source family, exact candidate transitions and chosen zero anchor,
    # but not the generated encoding table. It recovers that entire table.
    public = {"source": source, "cases": [
        {"transitions": [catalog[i]["table"] for i in c["updates"]], "root": c["root"]}
        for c in solutions]}
    dump(out / "attack.public.json", public)
    attacked = subprocess.run([sys.executable, str(ROOT / "conjugacy.py")],
                             input=json.dumps(public), capture_output=True, text=True,
                             check=True, timeout=protocol["limits"]["attack_seconds"])
    recovered = json.loads(attacked.stdout)
    assert recovered == [c["encoding"] for c in solutions]
    dump(out / "attack.recovered.json", recovered)
    dump(out / "catalog.json", catalog)
    dump(out / "pair-records.json", pair_records)
    dump(out / "solutions.json", solutions)
    if solutions:
        chosen = next((c for c in solutions if c["encoding_in_update_catalog"] is None), solutions[0])
        target = [catalog[i]["table"] for i in chosen["updates"]]
        sample = {"source": source, "solution": chosen,
                  "programs": [catalog[i]["program"] for i in chosen["updates"]],
                  "transitions": target,
                  "checks": [{"label": i, "x": x, "encoded_x": chosen["encoding"][x],
                              "expected": chosen["encoding"][source[i][x]],
                              "actual": target[i][chosen["encoding"][x]]}
                             for i in range(2) for x in states]}
        dump(out / "sample.json", sample)
    result = {"python": platform.python_version(), "platform": platform.platform(),
              "syntax_programs": len(programs), "distinct_transition_tables": len(catalog),
              "eligible_per_label": [len(v) for v in eligible], "root_attempts": attempts,
              "accepted_pairs": sum(bool(c["valid_roots"]) for c in pair_records),
              "encodings": len(solutions),
              "encodings_not_in_update_catalog": sum(c["encoding_in_update_catalog"] is None for c in solutions),
              "verified_transitions": len(solutions) * n * 2,
              "attack_recovered": len(recovered), "tiny_control_cases": control_count,
              "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                for name in ["search.py", "conjugacy.py", "protocol.json"]}}
    dump(out / "results.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
