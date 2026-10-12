"""Output-aware audit of saved root sets, using no imports from check.py."""
import hashlib
import itertools
import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = ROOT / "projection-results.json"
    if out.exists():
        raise FileExistsError(out)
    protocol = json.loads((ROOT / "projection-protocol.json").read_text())
    assert digest(ROOT / "classifications.json") == protocol["input_sha256"]
    saved = json.loads((ROOT / "classifications.json").read_text())
    coefficients = saved["coefficients"]
    points = list(itertools.product(range(4), repeat=2))
    # Independent evaluation of each polynomial truth table, then each saved intersection.
    tables = [[sum(c*t for c,t in zip(cs, (1,x,y,x*y,x*x,y*y))) % 4
               for x,y in points] for cs in coefficients]
    decode = [lambda x,y:x, lambda x,y:(x+y)%4, lambda x,y:(x+y*y)%4]
    derivatives = [(1,0), (1,1), (1,0)]  # mod2; d(y^2)/dy = 0
    stats = [{"name": name, "nonempty": 0, "global_unique": 0,
              "global_unique_multiroot": 0, "local_pass": 0,
              "local_pass_global_fail": 0, "first_counterexample": None}
             for name in protocol["decoders"]]
    records = []
    assert len(saved["systems"]) == 65536
    seen = set()
    for i,j,mask in saved["systems"]:
        assert (i,j) not in seen
        seen.add((i,j))
        indices = [k for k in range(16) if tables[i][k] == tables[j][k] == 0]
        assert mask == sum(1 << k for k in indices)
        roots = [points[k] for k in indices]
        if not roots:
            continue  # No root is not a valid implementation.
        kernels = []
        for x,y in roots:
            rows = [(coefficients[q][1]+coefficients[q][3]*y,
                     coefficients[q][2]+coefficients[q][3]*x) for q in (i,j)]
            kernels.append([(u,v) for u,v in itertools.product(range(2), repeat=2)
                            if all((a*u+b*v)%2 == 0 for a,b in rows)])
        classifications = []
        for d, deriv, stat in zip(decode, derivatives, stats):
            outputs = sorted({d(x,y) for x,y in roots})
            unique = len(outputs) == 1
            local = all((deriv[0]*u + deriv[1]*v)%2 == 0
                        for k in kernels for u,v in k)
            assert not unique or local
            stat["nonempty"] += 1
            stat["global_unique"] += unique
            stat["global_unique_multiroot"] += unique and len(roots)>1
            stat["local_pass"] += local
            stat["local_pass_global_fail"] += local and not unique
            if local and not unique and stat["first_counterexample"] is None:
                stat["first_counterexample"] = {"coefficients": [coefficients[i],coefficients[j]],
                    "roots": roots, "outputs": outputs, "kernels": kernels}
            classifications.append([outputs, local])
        records.append([i,j,classifications])
    def roots_of(c,d):
        return [(x,y) for x,y in points
                if all(sum(a*t for a,t in zip(cs,(1,x,y,x*y)))%4 == 0 for cs in (c,d))]
    controls = {"redundant": roots_of([0,1,0,0],[0,0,0,0]),
                "local_insufficient": roots_of([3,1,1,0],[0,0,0,1])}
    assert controls["redundant"] == [(0,0),(0,1),(0,2),(0,3)]
    assert controls["local_insufficient"] == [(0,1),(1,0)]
    report = {"python": platform.python_version(), "systems_verified": len(seen),
              "decoders": stats, "controls": controls, "records": records,
              "hashes": {n:digest(ROOT/n) for n in
                         ("projection_check.py","projection-protocol.json","classifications.json")}}
    out.write_text(json.dumps(report, separators=(",",":")) + "\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("records","hashes")}, indent=2))


if __name__ == "__main__":
    main()
