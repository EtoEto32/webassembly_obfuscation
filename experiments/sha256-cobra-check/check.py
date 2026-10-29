"""Extract bounded pure subexpressions from binary disassembly and run CoBRA."""
import ast
import hashlib
import itertools
import json
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
BASE = ROOT.parent / "sha256-research-baseline/artifacts"
OUT = ROOT / "artifacts"
DOCKER = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
WABT = REPO / ".tools/wabt-1.0.42/bin/wasm2wat.exe"
MASK = (1 << 32) - 1
OPS = {"i32.add": "+", "i32.sub": "-", "i32.mul": "*", "i32.xor": "^",
       "i32.and": "&", "i32.or": "|", "i32.shl": "<<", "i32.shr_u": ">>"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def parse_wat(text):
    stack, roots = [], []
    pattern = r'\s+|;;[^\n]*|\(;.*?;\)|"(?:\\.|[^"\\])*"|[()]|[^\s()]+'
    for token in re.findall(pattern, text, flags=re.S):
        if token.isspace() or token.startswith((";;", "(;")):
            continue
        if token == "(":
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ")":
            stack.pop()
        else:
            stack[-1].append(token)
    assert not stack and len(roots) == 1
    return roots[0]


def convert(node, variables):
    if not isinstance(node, list) or not node:
        raise ValueError("not expression")
    op = node[0]
    if op == "local.get" and len(node) == 2:
        if node[1] not in variables:
            variables[node[1]] = f"v{len(variables)}"
        return variables[node[1]], 0
    if op == "i32.const" and len(node) == 2:
        return str(int(node[1], 0) & MASK), 0
    if op not in OPS or len(node) != 3:
        raise ValueError("outside pure subset")
    left, lc = convert(node[1], variables)
    if op in ("i32.shl", "i32.shr_u"):
        if node[2][0] != "i32.const":
            raise ValueError("variable shift")
        right, rc = str(int(node[2][1], 0) & 31), 0
    else:
        right, rc = convert(node[2], variables)
    return f"({left}{OPS[op]}{right})", lc + rc + 1


def extract(node, location=()):
    if not isinstance(node, list):
        return
    variables = {}
    try:
        expr, cost = convert(node, variables)
        if 1 <= cost <= 8 and 1 <= len(variables) <= 2:
            yield {"expression": expr, "cost": cost, "locals": variables,
                   "tree_path": location, "tree": node}
    except (ValueError, TypeError, IndexError):
        pass
    for i, child in enumerate(node):
        if isinstance(child, list):
            yield from extract(child, location + (i,))


def evaluate(node, values):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value & MASK
    if isinstance(node, ast.Name):
        return values[node.id]
    if isinstance(node, ast.UnaryOp):
        x = evaluate(node.operand, values)
        if isinstance(node.op, ast.Invert): return (~x) & MASK
        if isinstance(node.op, ast.USub): return (-x) & MASK
        if isinstance(node.op, ast.UAdd): return x
    if isinstance(node, ast.BinOp):
        a, b = evaluate(node.left, values), evaluate(node.right, values)
        if isinstance(node.op, ast.Add): return (a + b) & MASK
        if isinstance(node.op, ast.Sub): return (a - b) & MASK
        if isinstance(node.op, ast.Mult): return a * b & MASK
        if isinstance(node.op, ast.BitXor): return a ^ b
        if isinstance(node.op, ast.BitAnd): return a & b
        if isinstance(node.op, ast.BitOr): return a | b
        if isinstance(node.op, (ast.LShift, ast.RShift)):
            if not isinstance(node.right, ast.Constant) or not 0 <= b < 32:
                raise ValueError("output shift outside supported subset")
            return ((a << b) if isinstance(node.op, ast.LShift) else (a >> b)) & MASK
    raise ValueError("unsupported returned expression")


def main():
    OUT.mkdir(exist_ok=False)
    protocol = json.loads((ROOT / "protocol.json").read_text())
    image = subprocess.run([DOCKER, "image", "inspect", protocol["image"], "--format", "{{.Id}}"],
                           check=True, text=True, capture_output=True, timeout=20).stdout.strip()
    assert image == protocol["image_id"]
    selection, cache = [], {}
    for binary in sorted(BASE.glob("*.wasm")):
        wat = subprocess.run([str(WABT), str(binary), "--fold-exprs"], capture_output=True,
                             text=True, check=True, timeout=20).stdout
        (OUT / (binary.name + ".wat")).write_text(wat, encoding="utf-8")
        found = list(extract(parse_wat(wat)))
        unique = {r["expression"]: r for r in reversed(found)}
        chosen = sorted(unique.values(), key=lambda r: (-r["cost"], r["expression"]))[:4]
        selection.append({"binary": binary.name, "sha256": digest(binary),
                          "eligible_occurrences": len(found), "eligible_unique": len(unique), "selected": chosen})
        for row in chosen: cache.setdefault(row["expression"], None)
    save("selection.json", selection)
    boundary = [0, 1, 2, MASK, MASK - 1, 1 << 31, (1 << 31) - 1]
    rng = random.Random(protocol["seed"])
    points = [dict(v0=a, v1=b) for a, b in itertools.product(boundary, repeat=2)]
    points += [dict(v0=rng.getrandbits(32), v1=rng.getrandbits(32)) for _ in range(256)]
    save("points.json", points)
    for idx, expr in enumerate(cache):
        command = [DOCKER, "run", "--rm", "--network", "none", "--read-only", "--memory", "512m",
                   "--cpus", "1", "--pids-limit", "128", "--entrypoint", "/usr/bin/timeout",
                   protocol["image"], "25s", "/build/tools/cobra-cli/cobra-cli", "--mba", expr, "--bitwidth", "32"]
        r = subprocess.run(command, capture_output=True, text=True, timeout=40)
        status = "returned" if r.returncode == 0 else "error"
        if "Unsupported:" in r.stderr: status = "unsupported"
        if r.returncode == 124: status = "timeout"
        item = {"input": expr, "stdout": r.stdout, "stderr": r.stderr, "exit": r.returncode, "status": status}
        if status == "returned":
            try:
                before, after = [ast.parse(s.strip(), mode="eval").body for s in [expr, r.stdout]]
                values = [{"input": p, "before": evaluate(before, p), "after": evaluate(after, p)} for p in points]
                item["mismatches"] = sum(v["before"] != v["after"] for v in values)
                item["checks"] = len(values)
                item["input_cost"], item["output_cost"] = [sum(isinstance(n, (ast.BinOp, ast.UnaryOp)) for n in ast.walk(t)) for t in [before, after]]
                item["reduced"] = item["mismatches"] == 0 and item["output_cost"] < item["input_cost"]
                save(f"case{idx}.values.json", values)
            except (ValueError, SyntaxError, KeyError) as exc:
                item["status"] = "validation-unsupported"
                item["validation_error"] = str(exc)
        cache[expr] = item
        save(f"case{idx}.json", item)
    result = {"image_id": image, "unique_cli_calls": len(cache), "cases": list(cache.values()),
              "source_sha256": {name: digest(ROOT / name) for name in ["check.py", "protocol.json"]},
              "binary_summary": [{"binary": s["binary"], "selected": len(s["selected"]),
                                  "reduced": sum(cache[r["expression"]].get("reduced", False) for r in s["selected"])} for s in selection]}
    save("results.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
