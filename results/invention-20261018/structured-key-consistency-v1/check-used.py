"""Structural feasibility of a restricted branch-independent key schedule.

Not a Wasm obfuscator or a reproduction/attack of WBLO. Standard library only.
Refuses to replace an existing result directory.
"""
import argparse
import hashlib
import itertools
import json
import platform
import random
import time
from pathlib import Path


def classify(edges):
    n = len(edges)
    parent = list(range(n))

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    unions = []
    for u, successors in enumerate(edges):
        if successors:
            for v in successors[1:]:
                a, b = root(successors[0]), root(v)
                if a != b:
                    parent[b] = a
                    unions.append([u, successors[0], v])
    roots = [root(u) for u in range(n)]
    names = {r: i for i, r in enumerate(sorted(set(roots)))}
    keys = [names[r] for r in roots]
    seen = {}
    for u, successors in enumerate(edges):
        if successors:
            pair = (keys[u], keys[successors[0]])
            if pair in seen:
                return {"feasible": False, "keys": keys, "unions": unions,
                        "collision": [seen[pair], u], "key_pair": list(pair)}
            seen[pair] = u

    # Construct one total update table, a permutation of state codes per key.
    table = []
    for key in range(n):
        row = [None] * n
        for u, successors in enumerate(edges):
            if successors and keys[u] == key:
                row[u] = keys[successors[0]]
        remaining = iter(v for v in range(n) if v not in row)
        table.append([next(remaining) if v is None else v for v in row])
    return {"feasible": True, "keys": keys, "unions": unions, "table": table}


def partitions(n):
    """All restricted-growth strings, independent of graph/union-find."""
    if n == 0:
        yield ()
        return
    def extend(prefix, maximum):
        if len(prefix) == n:
            yield tuple(prefix)
        else:
            for k in range(maximum + 2):
                yield from extend(prefix + [k], max(maximum, k))
    yield from extend([0], 0)


def oracle(edges, assignments):
    # Enumerate every equality pattern of keys, then check the defining
    # deterministic and injectivity requirements directly on every edge.
    for keys in assignments:
        forward, backward = {}, {}
        valid = True
        for u, successors in enumerate(edges):
            for v in successors:
                arg = (keys[u], u)
                out = keys[v]
                if arg in forward and forward[arg] != out:
                    valid = False
                    break
                inv = (keys[u], out)
                if inv in backward and backward[inv] != u:
                    valid = False
                    break
                forward[arg] = out
                backward[inv] = u
            if not valid:
                break
        if valid:
            return True
    return False


def verify_construction(edges, result):
    if not result["feasible"]:
        # Check the collision against independently accumulated required
        # key equalities using undirected reachability, not union-find.
        n = len(edges)
        neighbors = [set() for _ in range(n)]
        for succ in edges:
            for a, b in itertools.combinations(succ, 2):
                neighbors[a].add(b)
                neighbors[b].add(a)
        def connected(a, b):
            todo, visited = [a], set()
            while todo:
                x = todo.pop()
                if x == b:
                    return True
                if x not in visited:
                    visited.add(x)
                    todo.extend(neighbors[x] - visited)
            return False
        a, b = result["collision"]
        assert a != b and connected(a, b)
        assert edges[a] and edges[b] and connected(edges[a][0], edges[b][0])
    else:
        keys, table = result["keys"], result["table"]
        for row in table:
            assert sorted(row) == list(range(len(edges)))
        for u, succ in enumerate(edges):
            for v in succ:
                assert table[keys[u]][u] == keys[v]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    rng = random.Random(0x53544B43)
    samples = {
        "line": [[1], [2], [3], []],
        "diamond": [[1, 2], [3], [3], []],
        "cycle": [[1], [2], [0]],
        "branch_to_distinct_terminals": [[1, 2], [], []],
        "branch_then_self_loops": [[1, 2], [1], [2]],
        "diamond_in_loop": [[1, 2], [3], [3], [0]],
        "two_separate_branches": [[1, 2], [3], [4], [], []],
    }
    details = {}
    for name, edges in samples.items():
        result = classify(edges)
        verify_construction(edges, result)
        assert result["feasible"] == oracle(edges, list(partitions(len(edges))))
        details[name] = {"edges": edges, **result}

    corpus = []
    for n in range(1, 4):
        for mask in range(1 << (n * n)):
            corpus.append(("exhaustive", [[v for v in range(n)
                           if mask & (1 << (u * n + v))] for u in range(n)]))
    for n in range(4, 8):
        for _ in range(128):
            density = rng.choice([0.1, 0.25, 0.5, 0.75])
            corpus.append(("seeded", [[v for v in range(n) if rng.random() < density]
                                    for u in range(n)]))

    assignments = {n: list(partitions(n)) for n in range(1, 8)}
    rows = []
    for kind, edges in corpus:
        result = classify(edges)
        expected = oracle(edges, assignments[len(edges)])
        verify_construction(edges, result)
        assert result["feasible"] == expected
        rows.append({"kind": kind, "edges": edges, "feasible": expected})

    # Removing a premise really can escape the obstruction. These are
    # mathematical controls, not new obfuscation mechanisms.
    diamond = samples["diamond"]
    # Noninjective in state: K(A)=0, K(B)=K(C)=1, K(D)=2.
    keys = [0, 1, 1, 2]
    noninjective = {(0, 0): 1, (1, 1): 2, (1, 2): 2}
    for u, succ in enumerate(diamond):
        for v in succ:
            assert noninjective[(keys[u], u)] == keys[v]
    # An edge-conditioned update can assign distinct keys to all four states.
    distinct_keys = [0, 1, 2, 3]
    edge_table = {(u, v): distinct_keys[v] for u, succ in enumerate(diamond) for v in succ}
    for u, succ in enumerate(diamond):
        for v in succ:
            assert edge_table[(u, v)] == distinct_keys[v]

    script = Path(__file__).read_bytes()
    report = {
        "date": "2026-10-18", "python": platform.python_version(),
        "platform": platform.platform(), "script_sha256": hashlib.sha256(script).hexdigest(),
        "seed": "0x53544B43", "elapsed_seconds": time.perf_counter() - start,
        "exhaustive_graphs": sum(row["kind"] == "exhaustive" for row in rows),
        "seeded_graphs": sum(row["kind"] == "seeded" for row in rows),
        "feasible_graphs": sum(row["feasible"] for row in rows),
        "mismatches": 0, "named_cases": details, "graphs": rows,
        "controls": {"noninjective_diamond": "passes", "edge_conditioned_diamond": "passes"},
        "scope": "Finite graph model; no Wasm run, no WBLO implementation or attack."
    }
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output / "check-used.py").write_bytes(script)
    print(json.dumps({k: report[k] for k in ["exhaustive_graphs", "seeded_graphs", "feasible_graphs", "mismatches", "elapsed_seconds"]}))


if __name__ == "__main__":
    main()
