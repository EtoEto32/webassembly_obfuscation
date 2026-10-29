import hashlib
import importlib.util
import json
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent
HELPER = HERE.parent/'sha-history-gate/check.py'
OUTPUT = HERE/'bridge-results.json'


def main():
    assert not OUTPUT.exists()
    spec = importlib.util.spec_from_file_location('history', HELPER)
    history = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(history)
    protocol = json.loads((HERE/'bridge-protocol.json').read_text())
    rows = []
    for t in range(1, 32):
        b = max(22, t)
        v = 1 << b
        # q(x,0,0)=Sigma0(x); reuse actual 32-bit SHA helper.
        sigma = history.q(v, 0, 0)
        # All three rotations avoid wrap for this witness, so this expression
        # independently states the exact set bits without invoking rotate.
        expected = sum(1 << (b-r) for r in (2, 13, 22))
        assert sigma == expected
        assert v % (1 << t) == 0
        assert sigma % (1 << t) != 0
        assert (sigma & -sigma).bit_length()-1 == b-22 < t
        rows.append({'subgroup_threshold': t, 'input_bit': b, 'input': v,
                     'Sigma0': sigma, 'outside_residue': sigma % (1 << t),
                     'lowest_output_bit': b-22})
    # Endpoint controls: {0} and the entire word group are invariant.
    assert history.q(0, 0, 0) == 0
    assert all(0 <= row['Sigma0'] < 2**32 for row in rows)
    results = {'python': platform.python_version(), 'protocol': protocol,
               'witnesses': rows, 'proper_subgroups_checked': len(rows),
               'endpoint_controls': ['zero subgroup', 'whole group'],
               'source_hashes': {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [Path(__file__).resolve(), HERE/'bridge-protocol.json', HELPER]}}
    OUTPUT.write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps({'proper_subgroups_checked': len(rows),
                      'quotient_width_2': rows[1], 'embedding_width_2': rows[29]}))


if __name__ == '__main__':
    main()
