from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent


def main():
    output = HERE/'results.json'
    assert not output.exists()
    protocol = json.loads((HERE/'protocol.json').read_text())
    rows = []
    for w in protocol['widths']:
        modulus = 1 << w
        counts = Counter()
        first = {}
        for x in range(modulus):
            for y in range(modulus):
                a, b = x, y
                trace = [[a, b]]
                for step in range(1, 6):
                    try:
                        inv = pow(a, -1, modulus)
                    except ValueError:
                        assert a % 2 == 0
                        counts[step] += 1
                        first.setdefault(step, {'input': [x,y], 'trace': trace, 'nonunit': a})
                        break
                    assert a*inv % modulus == 1
                    a, b = b, (1+b)*inv % modulus
                    trace.append([a,b])
                else:
                    counts['completed'] += 1
        expected = {1: modulus**2//2, 2: modulus**2//4, 3: modulus**2//4}
        assert dict(counts) == expected
        rows.append({'width': w, 'pairs': modulus**2,
                     'first_undefined_step_counts': dict(counts), 'witnesses': first})
    controls = []
    for x, y in protocol['rational_controls']:
        a,b = Fraction(x), Fraction(y)
        trace = [[str(a),str(b)]]
        for _ in range(5):
            a,b = b,(1+b)/a
            trace.append([str(a),str(b)])
        assert (a,b) == (x,y)
        controls.append({'input': [x,y], 'trace': trace})
    result = {'python': platform.python_version(), 'modular_rows': rows,
              'total_pairs': sum(r['pairs'] for r in rows), 'completed_modular_orbits': 0,
              'rational_controls': controls,
              'source_hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [Path(__file__).resolve(), HERE/'protocol.json']}}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'total_pairs': result['total_pairs'], 'completed_modular_orbits': 0,
                      'rational_controls': len(controls)}))


if __name__ == '__main__':
    main()
