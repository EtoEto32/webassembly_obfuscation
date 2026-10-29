"""Static public-IR quotient, followed by the existing finite-support attack.

No generator imports, original gates, matrices, traces or expected outputs.
"""
import copy, hashlib, json, subprocess, sys
from pathlib import Path

def project(p):
    if p['modulus'] != 1 << 32:
        raise ValueError('Only the declared i32 ring is supported')
    if p.get('scaling') not in (None, 'odd-input-and-gate-v1'):
        raise ValueError('Unknown scaling rule')
    q = copy.deepcopy(p)
    q.pop('scaling', None)
    q['modulus'] = 2
    for n in q['inputs']:
        n['columns'] = [[v & 1 for v in col] for col in n['columns']]
        if len(set(map(tuple, n['columns']))) != 2:
            raise ValueError('Input columns collapse in quotient')
    for n in q['constants']:
        n['value'] = [v & 1 for v in n['value']]
    for n in q['nodes']:
        n['tensor'] = [[v & 1 for v in row] for row in n['tensor']]
    for n in q['outputs']:
        n['decoder'] = [v & 1 for v in n['decoder']]
    return q

if __name__ == '__main__':
    source, quotient, output = map(Path, sys.argv[1:4])
    if quotient.exists() or output.exists():
        raise SystemExit('Refuse overwrite')
    blob = source.read_bytes()
    q = project(json.loads(blob))
    quotient.write_text(json.dumps(q, indent=2))
    recovery = Path(__file__).resolve().parents[1] / 'tensor-support-gate' / 'recover.py'
    subprocess.run([sys.executable, str(recovery), str(quotient), str(output)], check=True, timeout=30)
    result = json.loads(output.read_text())
    result['source_public_sha256'] = hashlib.sha256(blob).hexdigest()
    result['projection'] = 'componentwise modulo 2; declared odd factors map to 1'
    output.write_text(json.dumps(result, indent=2))
