"""Counterexample to exchanging two complete SHA-256 round injections.

This is a pre-implementation rejection test, not a new obfuscated Wasm build.
"""
import hashlib
import importlib.util
import json
import platform
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HELPER = ROOT / 'experiments/sha-joint-history-gate/check.py'
SPEC = importlib.util.spec_from_file_location('sha_helpers', HELPER)
sha = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sha)


def main():
    output = HERE / 'results.json'
    if output.exists():
        raise FileExistsError(output)
    message = bytes.fromhex('0000000000000001')
    padded = sha.padded(message)
    assert len(padded) == 64
    normal, words = sha.normal(padded, sha.IV)
    injections = [(k + w) & sha.MASK for k, w in zip(sha.K, words)]
    changed = [injections[1], injections[0]] + injections[2:]
    after = [sha.IV[:]]
    for injection in changed:
        after.append(sha.old.reference(after[-1], injection))

    def digest(states):
        return b''.join(((a+b) & sha.MASK).to_bytes(4, 'big')
                        for a, b in zip(sha.IV, states[-1])).hex()

    expected = hashlib.sha256(message).hexdigest()
    before_digest = digest(normal)
    after_digest = digest(after)
    assert before_digest == expected
    assert injections[0] != injections[1]
    # The final b after two rounds records a after the first round.
    delta_b = (after[2][1] - normal[2][1]) & sha.MASK
    assert delta_b == (injections[1] - injections[0]) & sha.MASK
    assert all(normal[i] != after[i] for i in range(1, 65))
    assert after_digest != expected
    sources = [Path(__file__), HELPER,
               ROOT / 'experiments/sha-history-gate/check.py',
               ROOT / 'experiments/sha256-research-baseline/vendor/sha256.js']
    report = {
        'python': platform.python_version(),
        'experiment': 'one full single-block Python counterexample; no Wasm run',
        'message_hex': message.hex(), 'padded_hex': padded.hex(),
        'first_two_original_injections': injections[:2],
        'first_two_exchanged_injections': changed[:2],
        'delta_b_at_boundary_2': delta_b,
        'standard_sha256': expected, 'before_sha256': before_digest,
        'exchanged_sha256': after_digest,
        'original_states': normal, 'exchanged_states': after,
        'source_hashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
    }
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ('original_states', 'exchanged_states')}, indent=2))


if __name__ == '__main__':
    main()
