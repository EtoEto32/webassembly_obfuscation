import hashlib
import importlib.util
import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HELPER = ROOT.parent / 'sha-history-gate' / 'check.py'
M = (1 << 32) - 1

def sigma(x):
    bits = f'{x:032b}'
    return int(bits[-2:]+bits[:-2], 2) ^ int(bits[-13:]+bits[:-13], 2) ^ int(bits[-22:]+bits[:-22], 2)

def main():
    target = ROOT / 'results.json'
    if target.exists():
        raise FileExistsError(target)
    spec = importlib.util.spec_from_file_location('round_reference', HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    delta = [1] + [0]*7
    for base_a in (0, 3):
        base = [base_a] + [0]*7
        shifted = [(a+b)&M for a,b in zip(base, delta)]
        before = module.reference(base, 0)
        after = module.reference(shifted, 0)
        difference = [(a-b)&M for a,b in zip(after, before)]
        expected = [(sigma(base_a+1)-sigma(base_a))&M, 1] + [0]*6
        assert difference == expected
        recovered = [(a+d)&M for a,d in zip(base, delta)]
        assert recovered == shifted
        rows.append(dict(base=base, shifted=shifted, base_output=before,
                         shifted_output=after, difference=difference,
                         independent_expected=expected, recovered=recovered))
    assert rows[0]['difference'] != rows[1]['difference']
    result = dict(python=platform.python_version(), combined_input=0, delta=delta,
                  rows=rows, base_independent_update_refuted=True,
                  sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [ROOT/'check.py', ROOT/'README.md', HELPER]})
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'differences':[r['difference'] for r in rows], 'refuted':True}))

if __name__ == '__main__':
    main()
