"""Finite semantic gate, not an obfuscator or a security benchmark."""
import hashlib
import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def original(x, branch, u):
    # Independent full-state reference; branch is a future input.
    n = x % 16 if branch == 0 else x // 16
    return (n + 2 * n * n + u) % 16


def project(x, branch):
    return (x >> (4 * branch)) & 15


def transformed(r, u):
    return (r * (1 + (r << 1)) + u) & 15


def partition(futures):
    groups = {}
    for x in range(256):
        signature = tuple(original(x, b, u) for b, u in futures)
        groups.setdefault(signature, []).append(x)
    return list(groups.values())


def main():
    target = ROOT / 'results.json'
    if target.exists():
        raise SystemExit('Preserve existing results: use a fresh directory.')
    checks = 0
    for x in range(256):
        for b in range(2):
            for u in range(16):
                assert original(x, b, u) == transformed(project(x, b), u)
                checks += 1

    # State equivalence uses every possible continuation, not a sampled trace.
    unknown = partition([(b, u) for b in range(2) for u in range(16)])
    known = [partition([(b, u) for u in range(16)]) for b in range(2)]
    assert len(unknown) == 256
    assert [len(g) for g in known] == [16, 16]

    # Check an algebraic permutation claim independently by enumeration.
    polynomial_outputs = [transformed(r, 0) for r in range(16)]
    assert len(set(polynomial_outputs)) == 16

    # A proposed early projection must not merge distinguishable futures.
    witnesses = []
    for erased_branch in (0, 1):
        witness = None
        for x in range(256):
            for y in range(x + 1, 256):
                if project(x, erased_branch) != project(y, erased_branch):
                    continue
                for b in range(2):
                    if original(x, b, 0) != original(y, b, 0):
                        witness = dict(projection_branch=erased_branch, x=x, y=y,
                                       future_branch=b, u=0,
                                       outputs=[original(x, b, 0), original(y, b, 0)])
                        break
                if witness:
                    break
            if witness:
                break
        assert witness is not None
        witnesses.append(witness)

    result = dict(
        python=platform.python_version(), seed=None,
        scope='Finite 8-bit state; one future branch and a 4-bit arithmetic input.',
        checks=checks, mismatches=0,
        branch_unknown_class_count=len(unknown),
        branch_known_class_counts=[len(g) for g in known],
        branch_unknown_classes=unknown, branch_known_classes=known,
        early_projection_counterexamples=witnesses,
        polynomial_outputs=polynomial_outputs,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        novelty='No new transformation mechanism demonstrated.',
        limitations=['No Wasm generated or executed.', 'No runtime or recovery benchmark.',
                     'Not a result about every non-injective representation.'])
    target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['checks', 'mismatches',
        'branch_unknown_class_count', 'branch_known_class_counts',
        'early_projection_counterexamples']}))


if __name__ == '__main__':
    main()
