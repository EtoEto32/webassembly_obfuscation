"""Finite checks supporting even-basin-reduction.md; not a Wasm test."""
import json
from pathlib import Path

rows = []
for w in range(2, 10):
    modulus = 1 << w
    half = modulus >> 1
    images = set()
    for a_half in range(half):
        for b_half in range(half):
            a, b = 2 * a_half, 2 * b_half
            q = ((a + a * (a + 1) * b) % modulus,
                 (b + b * (b + 1) * a) % modulus)
            v = ((a_half + 2*a_half*(2*a_half+1)*b_half) % half,
                 (b_half + 2*b_half*(2*b_half+1)*a_half) % half)
            assert q == (2*v[0], 2*v[1])
            residual_next = ((a-q[0]) % modulus, (b-q[1]) % modulus)
            normalized_next = ((a_half-v[0]) % half, (b_half-v[1]) % half)
            assert residual_next == tuple(2*x for x in normalized_next)
            images.add(v)
    assert len(images) == half * half
    rows.append({"wordBits": w, "evenResidualPairs": half*half,
                 "distinctNormalizedImages": len(images)})
report = {"scope": "Exhaustive finite even-basin checks, not Wasm execution",
          "checks": rows, "mismatches": 0}
Path(__file__).with_name("even-basin-results.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report))
