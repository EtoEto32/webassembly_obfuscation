import ast
import difflib
import json
import subprocess
from check import ROOT, OUT, WABT, convert, digest, parse_wat

DEST = OUT / "rewritten"
DEST.mkdir(exist_ok=False)
results = json.loads((OUT / "results.json").read_text())
rules = {r["input"]: ast.parse(r["stdout"].strip(), mode="eval").body
         for r in results["cases"] if r.get("reduced")}
operators = {ast.Add: "i32.add", ast.Sub: "i32.sub", ast.Mult: "i32.mul",
             ast.BitXor: "i32.xor", ast.BitAnd: "i32.and", ast.BitOr: "i32.or",
             ast.LShift: "i32.shl", ast.RShift: "i32.shr_u"}


def lower(t, local_map):
    if isinstance(t, ast.Name): return ["local.get", local_map[t.id]]
    if isinstance(t, ast.Constant): return ["i32.const", str(t.value & 0xffffffff)]
    if isinstance(t, ast.BinOp): return [operators[type(t.op)], lower(t.left, local_map), lower(t.right, local_map)]
    if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.USub): return ["i32.sub", ["i32.const", "0"], lower(t.operand, local_map)]
    if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.Invert): return ["i32.xor", ["i32.const", "-1"], lower(t.operand, local_map)]
    raise ValueError("unsupported output")


def render(t):
    return "(" + " ".join(map(render, t)) + ")" if isinstance(t, list) else t


def rewrite(t, changes):
    if not isinstance(t, list): return t
    mapping = {}
    try:
        expr, _ = convert(t, mapping)
        if expr in rules:
            replacement = lower(rules[expr], {v: k for k, v in mapping.items()})
            changes.append({"input": expr, "before": t, "after": replacement})
            return replacement
    except (ValueError, TypeError, IndexError):
        pass
    return [rewrite(x, changes) for x in t]


rows = []
for item in json.loads((OUT / "selection.json").read_text()):
    name = item["binary"]
    before = parse_wat((OUT / (name + ".wat")).read_text())
    changes = []
    after = rewrite(before, changes)
    old, new = render(before) + "\n", render(after) + "\n"
    (DEST / (name + ".wat")).write_text(new, encoding="utf-8")
    (DEST / (name + ".diff")).write_text("".join(difflib.unified_diff(
        old.splitlines(True), new.splitlines(True), fromfile="before", tofile="after")), encoding="utf-8")
    subprocess.run([str(WABT.with_name("wat2wasm.exe")), str(DEST / (name + ".wat")), "-o", str(DEST / name)], check=True, timeout=20)
    subprocess.run([str(WABT.with_name("wasm-validate.exe")), str(DEST / name)], check=True, timeout=20)
    rows.append({"binary": name, "input_sha256": item["sha256"], "output_sha256": digest(DEST / name),
                 "bytes": (DEST / name).stat().st_size, "rewrites": len(changes), "changes": changes})
(DEST / "manifest.json").write_text(json.dumps({"files": rows, "script_sha256": digest(ROOT / "rewrite.py"),
                                                "plan_sha256": digest(ROOT / "rewrite-plan.json")}, indent=2) + "\n")
print(json.dumps([{k: v for k, v in r.items() if k != "changes"} for r in rows], indent=2))
