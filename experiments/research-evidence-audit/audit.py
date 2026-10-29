"""Preservation and recorded-evidence checks, not an obfuscation success test."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPERIMENTS = ROOT.parent
REPO = EXPERIMENTS.parent


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "audit.json")
    out = parser.parse_args().out
    if out.exists():
        raise FileExistsError(out)
    checks = []
    def hashcheck(path, expected, origin):
        exists = path.is_file()
        checks.append({"path": path.relative_to(REPO).as_posix(), "origin": origin,
                       "exists": exists, "matches": exists and sha(path) == expected})
    inventories = []
    for inv in sorted(EXPERIMENTS.glob("*/inventory.json")):
        rows = read(inv)
        for row in rows:
            target = (inv.parent / row["path"]).resolve()
            assert target.is_relative_to(inv.parent.resolve())
            hashcheck(target, row["sha256"], inv.relative_to(REPO).as_posix())
        inventories.append({"path": inv.relative_to(REPO).as_posix(), "entries": len(rows), "sha256": sha(inv)})
    for folder, record in [
        ("group-order-gate", "artifacts/results.json"),
        ("joint-transition-search", "artifacts/results.json"),
        ("joint-transition-search", "lift-artifacts/results.json"),
        ("sha256-cobra-check", "artifacts/results.json")]:
        base = EXPERIMENTS / folder
        result = read(base / record)
        for name, expected in result["source_sha256"].items():
            hashcheck(base / name, expected, f"{folder}/{record}")
    # Independently check the stored transition certificates, not solver success flags.
    joint = EXPERIMENTS / "joint-transition-search/artifacts"
    source = read(joint / "attack.public.json")["source"]
    catalog, solutions = read(joint / "catalog.json"), read(joint / "solutions.json")
    transitions = 0
    for solution in solutions:
        e = solution["encoding"]
        assert sorted(e) == list(range(64))
        for label, idx in enumerate(solution["updates"]):
            for x in range(64):
                assert e[source[label][x]] == catalog[idx]["table"][e[x]]
                transitions += 1
    # Preserve negative results: expected mismatches must remain mismatches.
    lift = EXPERIMENTS / "joint-transition-search/lift-artifacts"
    lift_checks = 0
    for case in read(lift / "cases.json"):
        rows = read(lift / case["rows_file"])
        failures = [r for r in rows if r["actual"] != r["expected"]]
        assert len(rows) == case["checks"] and len(failures) == case["failures"]
        assert case["first_counterexample"] == (failures[0] if failures else None)
        lift_checks += len(rows)
    # Reconcile recorded full SHA outputs with hashed input data and actual binaries.
    base = EXPERIMENTS / "sha256-research-baseline/artifacts"
    index = read(base / "inputs.json")
    data = (base / "inputs.bin").read_bytes()
    assert hashlib.sha256(data).hexdigest() == index["bundle_sha256"]
    expected = {}
    for case in index["cases"]:
        message = data[case["offset"]:case["offset"] + case["length"]]
        assert hashlib.sha256(message).hexdigest() == case["expected"]
        expected[case["id"]] = case["expected"]
    cobra = EXPERIMENTS / "sha256-cobra-check/artifacts"
    selected = read(cobra / "selection.json")
    for entry in selected:
        hashcheck(base / entry["binary"], entry["sha256"], "CoBRA input provenance")
    rewritten = cobra / "rewritten"
    manifest = read(rewritten / "manifest.json")
    for entry in manifest["files"]:
        hashcheck(rewritten / entry["binary"], entry["output_sha256"], "CoBRA rewritten manifest")
    verification = read(rewritten / "verification.json")
    sha_checks = 0
    for result in verification["results"]:
        assert len(result["outputs"]) == len(expected) == result["checks"]
        assert len({r["id"] for r in result["outputs"]}) == len(expected)
        for row in result["outputs"]:
            assert row["actual"] == expected[row["id"]]
            sha_checks += 1
    for filename, expected_hash in [("rewrite.py", manifest["script_sha256"]),
                                    ("rewrite-plan.json", manifest["plan_sha256"]),
                                    ("verify.cjs", verification["script_sha256"])]:
        hashcheck(cobra.parent / filename, expected_hash, "CoBRA follow-up provenance")
    summaries = []
    for tree in [EXPERIMENTS, REPO / "tmp"]:
        for p in sorted(tree.glob("*/README.md")):
            summaries.append({"path": p.relative_to(REPO).as_posix(), "sha256": sha(p),
                              "scope": "indexed only; hash does not mean experiment rerun or content approved"})
    report = {"audit_script_sha256": sha(Path(__file__)), "inventories": inventories,
              "hash_checks": checks, "hash_failures": [r for r in checks if not r["matches"]],
              "recorded_transition_equations_checked": transitions,
              "recorded_lift_rows_recounted": lift_checks,
              "recorded_sha_outputs_reconciled": sha_checks, "readme_index": summaries,
              "runtime_tests_rerun": False, "goal_achieved": False}
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"inventories": len(inventories), "hash_checks": len(checks),
                      "hash_failures": len(report["hash_failures"]), "transition_checks": transitions,
                      "lift_rows": lift_checks, "sha_output_records": sha_checks,
                      "readmes_indexed": len(summaries)}, indent=2))
    if report["hash_failures"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
