"""Recheck saved evidence without importing the candidate implementation."""
import hashlib
import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent
M = 2**32 - 1


def sigma(x, rotations):
    result = 0
    for n in rotations:
        result ^= (x // (2**n)) | ((x % (2**n)) * 2**(32-n))
    return result


def term(a, b, c):
    return (sigma(a, (2, 13, 22)) + ((a & b) | (a & c) | (b & c))) & M


def main():
    saved = json.loads((ROOT / 'results.json').read_text())
    for name, digest in saved['hashes'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    cases = json.loads((ROOT / 'inputs-and-finals.json').read_text())
    first = json.loads((ROOT / 'example-trace.json').read_text())
    stream = hashlib.sha256()
    count = 0
    for index, case in enumerate(cases):
        state = case['initial'][:]
        p = state[:4]
        for j in range(4):
            p.append((state[j+4] - p[j] + term(*p[j+1:j+4])) & M)
        assert len(case['inputs']) == 64
        for step, u in enumerate(case['inputs']):
            a, b, c, d, e, f, g, h = state
            t = (h + sigma(e, (6, 11, 25)) + ((e & f) | ((M ^ e) & g)) + u) & M
            state = [(t + term(a,b,c)) & M, a,b,c,(t+d)&M,e,f,g]
            # A recurrence must shift the old history, then satisfy four equations.
            p = [state[0]] + p[:7]
            decoded = p[:4] + [(p[j]+p[j+4]-term(*p[j+1:j+4]))&M for j in range(4)]
            assert decoded == state
            row = dict(step=step, u=u, history=p, reference=state, recovered=decoded)
            if index == 0:
                assert row == first[step]
            stream.update(json.dumps(row, sort_keys=True, separators=(',', ':')).encode()+b'\n')
            count += 1
        assert p == case['final_history'] and state == case['final_reference']
    assert len(cases) == saved['states'] and count == saved['rounds']
    assert stream.hexdigest() == saved['all_trace_rows_sha256']
    result = dict(python=platform.python_version(), cases=len(cases), rounds=count,
                  input_hashes_verified=len(saved['hashes']), trace_digest=stream.hexdigest(),
                  scope='Saved trace consistency; no new independent attack or Wasm execution',
                  replay_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output = ROOT / 'replay-results.json'
    if output.exists():
        raise FileExistsError(output)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
