import hashlib
import json
import platform
from collections import Counter
from pathlib import Path
from check import partitions, rotr

ROOT = Path(__file__).resolve().parent


def canonical(items):
    seen = {}
    return [seen.setdefault(item, len(seen)) for item in items]


def main():
    output = ROOT / 'heterogeneous-results.json'
    if output.exists():
        raise FileExistsError(output)
    records = []
    summaries = []
    for w in (1,2,3):
        n = 1 << w
        histogram = Counter()
        checks = distinguishing = 0
        for q in partitions(n):
            rows = [tuple(q[(x+y)%n] for y in range(n)) for x in range(n)]
            inputs = canonical(rows)
            classes = max(inputs)+1
            table = {}
            for x in range(n):
                for y in range(n):
                    key = (inputs[x],inputs[y])
                    value = q[(x+y)%n]
                    assert table.setdefault(key,value) == value
                    checks += 1
            # Explicit context witnesses prove these row classes cannot merge.
            reps = [inputs.index(c) for c in range(classes)]
            witnesses = []
            for i,x in enumerate(reps):
                for z in reps[i+1:]:
                    y = next(y for y in range(n) if q[(x+y)%n] != q[(z+y)%n])
                    witnesses.append([x,z,y,q[(x+y)%n],q[(z+y)%n]])
                    distinguishing += 1
            assert inputs == [x%classes for x in range(n)]
            histogram[classes] += 1
            records.append(dict(width=w, output=q, input=inputs, witnesses=witnesses))
        summaries.append(dict(width=w, histogram=dict(sorted(histogram.items())),
                              operation_checks=checks, distinguishing_contexts=distinguishing))
    specs = {'Sigma0':((2,13,22),None), 'Sigma1':((6,11,25),None),
             'sigma0':((7,18),3), 'sigma1':((17,19),10)}
    requirements = []
    for name,(rotations,shift) in specs.items():
        def op(x):
            value = 0
            for r in rotations:
                value ^= rotr(x,r,32)
            if shift is not None:
                value ^= x >> shift
            return value
        for k in range(1,33):
            mask = (1<<k)-1
            support = [j for j in range(32) if op(1<<j)&mask]
            m = max(support)
            # An independent index-based support calculation, including XOR cancellation.
            index_support = set()
            for bit in range(k):
                row = set()
                for r in rotations:
                    index = (bit+r)%32
                    row.symmetric_difference_update([index])
                if shift is not None and bit+shift < 32:
                    row.symmetric_difference_update([bit+shift])
                index_support.update(row)
            assert set(support) == index_support
            assert op(1<<m)&mask != op(0)&mask
            requirements.append(dict(operation=name,output_bits=k,required_operand_bits=m+1,
                                     support=support,lower_bound_witness=[0,1<<m],
                                     witness_outputs=[op(0)&mask,op(1<<m)&mask]))
    data_path = ROOT/'heterogeneous-partitions.json'
    data_path.write_text(json.dumps(records,separators=(',',':'))+'\n')
    result = dict(python=platform.python_version(), summaries=summaries, requirements=requirements,
                  hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
                          ['check.py','heterogeneous.py','heterogeneous-protocol.json','heterogeneous-partitions.json']})
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(summaries=summaries,
                         first_full={name:next(r['output_bits'] for r in requirements if r['operation']==name and r['required_operand_bits']==32) for name in specs},
                         single_bit={r['operation']:r['required_operand_bits'] for r in requirements if r['output_bits']==1}),indent=2))


if __name__=='__main__':
    main()
