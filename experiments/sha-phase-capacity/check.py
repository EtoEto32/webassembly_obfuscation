"""Construct reachable SHA phase witnesses for a common-decoder capacity bound."""
import hashlib
import importlib.util
import itertools
import json
import platform
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HELPER = HERE.parent / 'sha-phase-witness/build.py'
spec = importlib.util.spec_from_file_location('witness', HELPER)
witness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(witness)
j = witness.joint
M = (1 << 32) - 1


def inverse(s, u, broken=False):
    A, B, C, D, E, F, G, H = s
    t1 = (A - j.old.q(B, C, D)) & M
    d = (E + t1 if broken else E - t1) & M
    h = (t1 - j.big1(F) - j.choice(F, G, H) - u) & M
    return [B, C, D, d, F, G, H, h]


def digest(message):
    chain = j.IV[:]
    padded = j.padded(message)
    for offset in range(0, len(padded), 64):
        states, _ = j.normal(padded[offset:offset+64], chain)
        chain = [(a + b) & M for a, b in zip(chain, states[-1])]
    return b''.join(x.to_bytes(4, 'big') for x in chain).hex()


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / 'artifacts'
    out.mkdir(parents=True, exist_ok=False)
    rng = random.Random(protocol['seed'])
    targets = [[0]*8, [M]*8, j.IV[:], [rng.getrandbits(32) for _ in range(8)]]
    phases = protocol['phases']
    assert len(set(j.K[i] for i in phases)) == len(phases)
    rows = []
    inverse_checks = negative_detected = pairs = 0
    for target_id, target in enumerate(targets):
        successors = []
        for phase in phases:
            previous = target[:]
            for i in reversed(range(8, phase)):
                prior = inverse(previous, j.K[i])
                assert j.old.reference(prior, j.K[i]) == previous
                negative_detected += j.old.reference(inverse(previous, j.K[i], True), j.K[i]) != previous
                inverse_checks += 1
                previous = prior
            words = witness.prefix(previous) + [0]*8
            message = b''.join(x.to_bytes(4, 'big') for x in words)
            states, schedule = j.normal(message, j.IV)
            assert states[phase] == target and schedule[phase] == 0
            expected_next = j.old.reference(target, j.K[phase])
            assert states[phase+1] == expected_next
            successors.append(expected_next)
            expected_digest = hashlib.sha256(message).hexdigest()
            assert digest(message) == expected_digest
            rows.append({'target_id': target_id, 'phase': phase, 'target': target,
                         'message_hex': message.hex(), 'W': schedule[phase],
                         'state8': states[8], 'next': expected_next, 'digest': expected_digest})
        for left, right in itertools.combinations(range(len(phases)), 2):
            assert successors[left] != successors[right]
            delta = (j.K[phases[left]] - j.K[phases[right]]) & M
            actual = [(a-b) & M for a,b in zip(successors[left], successors[right])]
            assert actual == [delta,0,0,0,delta,0,0,0]
            pairs += 1
    assert negative_detected > 0
    result = {'python': platform.python_version(), 'messages': len(rows),
              'full_digest_checks': len(rows), 'inverse_checks': inverse_checks,
              'wrong_inverse_detected': negative_detected, 'successor_pair_checks': pairs,
              'sampled_targets': len(targets), 'analytical_lower_bound_bits': 259,
              'universal_proof': 'README section 4; not established by enumerating these cases',
              'status': 'common-decoder 256-bit carrier rejected; no new obfuscator'}
    (out/'cases.json').write_text(json.dumps(rows, indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    sources = [Path(__file__).resolve(), HERE/'protocol.json', HELPER,
               witness.HELPER, j.HELPER, witness.BASE/'vendor/sha256.js']
    files = sources + [out/'cases.json', out/'results.json']
    manifest = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
