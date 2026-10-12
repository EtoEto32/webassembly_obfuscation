"""Bounded regression for rejecting exact homomorphic word encodings."""
import argparse
import hashlib
import json
import platform
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    protocol = json.loads((ROOT / "protocol.json").read_text())
    rng = random.Random(protocol["seed"])
    summaries = []
    for w, p, base in [(8, 65537, 3), (32, 18446744069414584321, 7)]:
        n = 1 << w
        g = pow(base, (p - 1) // n, p)
        assert pow(g, n, p) == 1 and pow(g, n // 2, p) != 1
        if w == 8:
            pairs = [(x, y) for x in range(n) for y in range(n)]
        else:
            boundary = [0, 1, 2, n // 2 - 1, n // 2, n - 2, n - 1, 0x55555555]
            pairs = [(x, y) for x in boundary for y in boundary]
            pairs += [(rng.randrange(n), rng.randrange(n)) for _ in range(256)]
        words = sorted({z for x, y in pairs for z in (x, y, (x + y) % n)})
        encoded = {x: pow(g, x, p) for x in words}
        # Shuffle so an enumeration order is not provided as a decoding table.
        order = list(words)
        rng.shuffle(order)
        public = {"width": w, "modulus": p, "generator": g,
                  "values": [encoded[x] for x in order]}
        save(args.out / f"w{w}.public.json", public)
        save(args.out / f"w{w}.private.json", {"words": order})
        attack = subprocess.run([sys.executable, str(ROOT / "recover.py")],
                                input=json.dumps(public), capture_output=True, text=True,
                                check=True, timeout=protocol["limits"]["attack_seconds"])
        recovered = json.loads(attack.stdout)
        assert [r["word"] for r in recovered["rows"]] == order
        assert all(r["lifting_squares"] == w * (w - 1) // 2 for r in recovered["rows"])
        save(args.out / f"w{w}.recovered.json", recovered)
        checks = []
        for x, y in pairs:
            expected = (x + y) & (n - 1)
            actual = encoded[x] * encoded[y] % p
            assert actual == encoded[expected]
            checks.append({"x": x, "y": y, "expected": expected,
                           "encoded_x": encoded[x], "encoded_y": encoded[y], "actual": actual})
        save(args.out / f"w{w}.checks.json", checks)
        save(args.out / f"w{w}.sample.json", next(r for r in checks if r["x"] == n - 1 and r["y"] == 1))
        bad = dict(public, values=[0])
        rejected = subprocess.run([sys.executable, str(ROOT / "recover.py")],
                                  input=json.dumps(bad), capture_output=True, text=True,
                                  timeout=protocol["limits"]["attack_seconds"])
        assert rejected.returncode != 0 and "outside generated subgroup" in rejected.stderr
        save(args.out / f"w{w}.invalid.json", {"input": bad, "stderr": rejected.stderr})
        summaries.append({"width": w, "addition_pairs": len(pairs), "values_recovered": len(words),
                          "mismatches": 0, "lifting_squares_per_value": w * (w - 1) // 2})
    # A smaller subgroup saves the homomorphism but loses injectivity.
    g8 = pow(3, 256, 65537)
    smaller = {"modulus": 65537, "generator": g8 * g8 % 65537,
               "x": 0, "y": 128}
    smaller["encoded_x"] = pow(smaller["generator"], smaller["x"], 65537)
    smaller["encoded_y"] = pow(smaller["generator"], smaller["y"], 65537)
    assert smaller["encoded_x"] == smaller["encoded_y"]
    # An odd-order group does not implement 4-bit modular wrap.
    odd = {"width": 4, "modulus": 23, "generator": 2, "x": 15, "y": 1,
           "actual": pow(2, 15, 23) * 2 % 23, "expected": 1}
    assert pow(2, 11, 23) == 1 and odd["actual"] != odd["expected"]
    save(args.out / "controls.json", {"smaller_order_collision": smaller, "odd_order_wrap_failure": odd})
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
              for name in ["check.py", "recover.py", "protocol.json"]}
    result = {"python": platform.python_version(), "platform": platform.platform(),
              "source_sha256": hashes, "results": summaries,
              "decision": "reject; no independent novelty or encoded-value concealment"}
    save(args.out / "results.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
