"""Emit and verify a concrete paired transition sample from saved search output."""
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
out = ROOT / "example"
out.mkdir(exist_ok=False)
catalog = json.loads((ROOT / "artifacts/catalog.json").read_text())
solutions = json.loads((ROOT / "artifacts/solutions.json").read_text())
public = json.loads((ROOT / "artifacts/attack.public.json").read_text())
solution = next(s for s in solutions if
                [catalog[i]["table"] for i in s["updates"]] != public["source"])
programs = [catalog[i]["program"] for i in solution["updates"]]
code = {
    "inc_a": "a = (a + 1) & M", "dec_a": "a = (a - 1) & M",
    "inc_b": "b = (b + 1) & M", "dec_b": "b = (b - 1) & M",
    "add_a_b": "a = (a + b) & M", "sub_a_b": "a = (a - b) & M",
    "xor_a_b": "a ^= b", "add_b_a": "b = (b + a) & M",
    "sub_b_a": "b = (b - a) & M", "xor_b_a": "b ^= a",
    "rot_a": "a = rol(a)", "rot_b": "b = rol(b)", "swap": "a, b = b, a",
    "xor_a_rol_b": "a ^= rol(b)", "xor_b_rol_a": "b ^= rol(a)",
    "mul_a_3": "a = (3 * a) & M", "mul_b_3": "b = (3 * b) & M"}
header = "W = 3\nM = (1 << W) - 1\ndef rol(v):\n    return ((v << 1) | (v >> (W - 1))) & M\n\n"
before = header + "def step(label, state):\n    a, b = state & M, state >> W\n    if label == 0:\n        a = (a + b) & M\n    elif label == 1:\n        a ^= rol(b)\n        b = (b + 1) & M\n    else:\n        raise ValueError(label)\n    return a | (b << W)\n"
after = header + "def step(label, state):\n    a, b = state & M, state >> W\n"
for i, program in enumerate(programs):
    after += ("    if" if i == 0 else "    elif") + f" label == {i}:\n"
    after += "".join("        " + code[op] + "\n" for op in program)
after += "    else:\n        raise ValueError(label)\n    return a | (b << W)\n"
(out / "before.py").write_text(before, encoding="utf-8")
(out / "after.py").write_text(after, encoding="utf-8")
(out / "before-after.diff").write_text("".join(difflib.unified_diff(
    before.splitlines(True), after.splitlines(True), fromfile="before.py", tofile="after.py")), encoding="utf-8")
before_env, after_env = {}, {}
exec(compile(before, "generated-before.py", "exec"), before_env)
exec(compile(after, "generated-after.py", "exec"), after_env)
e = solution["encoding"]
checks = []
for label in range(2):
    for x in range(64):
        plain = before_env["step"](label, x)
        encoded = after_env["step"](label, e[x])
        assert plain == public["source"][label][x]
        assert encoded == e[plain]
        checks.append({"label": label, "state": x, "encoded_state": e[x],
                       "plain_next": plain, "encoded_next": encoded})
certificate = {"selection": "first solution with updates different from source; explanatory post-run choice",
               "solution": solution, "programs": programs, "checks": checks,
               "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                 for name in ["emit_example.py", "artifacts/solutions.json", "artifacts/catalog.json"]},
               "generated_sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                                    for name in ["before.py", "after.py", "before-after.diff"]}}
(out / "certificate.json").write_text(json.dumps(certificate, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"checks": len(checks), "programs": programs, "root": solution["root"]}))
