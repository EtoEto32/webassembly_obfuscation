"""Finite countermodel for violating the ordinal variant's ordering precondition.

This does not schedule real Promise jobs or demonstrate an engine defect.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import shutil


def decode(order, groups):
    labels = [-1] * len(order)
    start = 0
    for label, (representative, count) in enumerate(groups):
        for i in order[start:start + count]:
            labels[i] = label
        if labels[representative] != label:
            return None
        start += count
    return labels


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for truth, groups in (([0, 0, 1, 1], [(0, 2), (2, 2)]),
                          ([0, 1, 0, 1], [(0, 2), (1, 2)])):
        outcomes = []
        for order in itertools.permutations(range(4)):
            labels = decode(order, groups)
            outcome = 'rejected' if labels is None else 'correct' if labels == truth else 'incorrect'
            outcomes.append({'order': order, 'labels': labels, 'outcome': outcome})
        counts = {name: sum(r['outcome'] == name for r in outcomes)
                  for name in ('correct', 'incorrect', 'rejected')}
        assert counts == {'correct': 4, 'incorrect': 4, 'rejected': 16}
        rows.append({'truth': truth, 'groups': groups, 'counts': counts, 'outcomes': outcomes})
    assert decode([0, 3, 2, 1], [(0, 2), (2, 2)]) == [0, 1, 1, 0]
    result = {'model': 'Artificial arbitrary permutation, intentionally violates same-agent reaction ordering',
              'engineFailure': False, 'rows': rows}
    (out/'results.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    shutil.copy2(__file__, out/'ordinal-order-audit.py')
    (out/'sha256.json').write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in out.iterdir() if p.is_file()}, indent=2), encoding='utf8')
    print(json.dumps([r['counts'] for r in rows]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    main(parser.parse_args().output)
