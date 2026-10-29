"""Independent bounded witness for an unbounded AST objective; not a SaMBA run."""
import hashlib
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    output = ROOT / 'cycle-results.json'
    if output.exists():
        raise SystemExit('Use a fresh directory; preserve existing results.')
    sources = {}
    rules = {}
    for name in ('eqsat.rs', 'batch_processing.rs'):
        blob = (ROOT / name).read_bytes()
        sources[name] = hashlib.sha256(blob).hexdigest()
        text = blob.decode()
        matches = re.findall(r'rewrite!\("([^"\n]+)";\s*"([^"\n]+)"\s*=>\s*"([^"\n]+)"\)', text)
        by_name = {n: [lhs, rhs] for n, lhs, rhs in matches}
        wanted = {
            'add-to-and-or': ['(+ ?x ?y)', '(+ (& ?x ?y) (| ?x ?y))'],
            'or-to-add': ['(| ?x ?y)', '(+ (+ ?x ?y) (+ 1 (| (~ ?x) (~ ?y))))'],
        }
        for n, pair in wanted.items():
            assert by_name[n] == pair
        # These two lines must be active, not merely commented-out matches.
        for n in wanted:
            lines = [line.strip() for line in text.splitlines() if f'rewrite!("{n}";' in line]
            assert len(lines) == 1 and lines[0].startswith('rewrite!')
        rules[name] = wanted

    # A finite grammar obtained using just those two equalities.
    graph = {
        'X': [('x',)], 'Y': [('y',)], 'One': [('1',)],
        'NX': [('~', 'X')], 'NY': [('~', 'Y')],
        'Z': [('|', 'NX', 'NY')], 'D': [('+', 'One', 'Z')],
        'B': [('&', 'X', 'Y')],
        'A': [('+', 'X', 'Y'), ('+', 'B', 'C')],
        'C': [('|', 'X', 'Y'), ('+', 'A', 'D')],
    }
    # Fixed 10 classes / 12 nodes; unfolding A -> B+(A+D) adds 12 AST nodes.
    sizes = [3 + 12 * k for k in range(17)]
    checks = {8: 0, 32: 0}
    rng = random.Random(0x53414D42)
    for width in (8, 32):
        mask = (1 << width) - 1
        pairs = ((x, y) for x in range(256) for y in range(256)) if width == 8 else (
            (rng.getrandbits(32), rng.getrandbits(32)) for _ in range(4096))
        for x, y in pairs:
            a, b, c = (x + y) & mask, x & y, x | y
            d = (1 + ((~x & mask) | (~y & mask))) & mask
            assert a == (b + c) & mask
            assert c == (a + d) & mask
            checks[width] += 2
            current = a
            for k in range(1, 17):
                current = (b + current + d) & mask
                assert current == a
                checks[width] += 1
    result = dict(
        author_revision='74ccd067f9d0b0b255f1140d0f581f499ed71cb9',
        sources_sha256=sources, checked_rules=rules, graph=graph,
        class_count=len(graph), enode_count=sum(map(len, graph.values())),
        unfolding_ast_sizes=sizes, negative_costs=[-n for n in sizes],
        finite_checks=checks, mismatches=0, seed=0x53414D42,
        conclusion='No largest finite AST in this finite cyclic grammar.',
        limitations=['Not an execution of egg or SaMBA.',
                     'Does not establish how often published experiments encounter the cycle.',
                     'A bounded extractor would be a baseline repair, not a new obfuscation algorithm.'])
    output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['class_count', 'enode_count', 'finite_checks', 'mismatches', 'unfolding_ast_sizes']}))


if __name__ == '__main__':
    main()
