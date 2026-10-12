"""Independent tiny GF(2) bilinear relation probe; not the authors' implementation."""
import json
import random
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 0x42494C49

def features(x, z, bits):
    result = 1 | (x << 1) | (z << (1+bits))
    for i in range(bits):
        if (x >> i) & 1:
            result |= z << (1+2*bits+i*bits)
    return result

def nullspace(rows, columns):
    pivots = {}
    for row in rows:
        while row:
            p = row.bit_length()-1
            if p in pivots:
                row ^= pivots[p]
            else:
                pivots[p] = row
                break
    basis = []
    for free in range(columns):
        if free in pivots:
            continue
        vector = 1 << free
        for p in sorted(pivots):
            if (pivots[p] & vector).bit_count() & 1:
                vector ^= 1 << p
        assert all((r & vector).bit_count() % 2 == 0 for r in rows)
        basis.append(vector)
    return basis

def affine(rng, bits):
    operations = [rng.sample(range(bits), 2) for _ in range(bits*4)]
    offset = rng.randrange(1 << bits)
    def apply(value):
        for target, source in operations:
            value ^= ((value >> source) & 1) << target
        return value ^ offset
    return apply

def main():
    destination = ROOT/'probe-results.json'
    if destination.exists():
        raise RuntimeError('Preserve existing results')
    rng = random.Random(SEED)
    rows = []
    for width in [3, 4]:
        bits = 2*width
        size = 1 << bits
        mask = (1 << width)-1
        columns = 1+2*bits+bits*bits
        for instance in range(3):
            encode_in, encode_out = affine(rng, bits), affine(rng, bits)
            def oracle(value):
                state = encode_in(value)
                x, y = state & mask, state >> width
                return encode_out(((x+y)&mask) | (y << width))
            pairs = [(x, oracle(x)) for x in range(size)]
            relations = nullspace([features(x,z,bits) for x,z in pairs], columns)
            # All pairs form the full-domain interpolation baseline. No held-out claim.
            unique = 0
            invalid = 0
            candidate_counts = []
            for x, expected in pairs:
                solutions = []
                for z in range(size):
                    v = features(x,z,bits)
                    if all((v & r).bit_count() % 2 == 0 for r in relations):
                        solutions.append(z)
                invalid += expected not in solutions
                unique += solutions == [expected]
                candidate_counts.append(len(solutions))
            rows.append(dict(width=width, instance=instance, queries=size,
                             monomials=columns, relation_dimension=len(relations),
                             unique_outputs=unique, invalid_outputs=invalid,
                             candidate_counts=candidate_counts,
                             oracle_pairs=pairs, relations=relations))
    result = dict(seed=SEED, experiment='full-domain small-width relation interpolation',
                  code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), cases=rows)
    destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps([{k:v for k,v in row.items() if k not in ['relations','oracle_pairs','candidate_counts']} for row in rows]))
    assert all(row['invalid_outputs']==0 and row['unique_outputs']==row['queries'] for row in rows)

if __name__=='__main__':
    main()
