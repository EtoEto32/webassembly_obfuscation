import hashlib
import json
from pathlib import Path
import platform
import random
import sys
from lift import lift

ROOT=Path(__file__).resolve().parent
SEED=0x4C494654

def main():
    destination=ROOT/'results.json'
    if destination.exists(): raise RuntimeError('Preserve existing results')
    source=Path(sys.argv[1])
    candidates=json.loads(source.read_text())['cases']
    rng=random.Random(SEED)
    records=[]
    for candidate in candidates:
        r1,r2=candidate['r1'],candidate['r2']
        def check(width,expected):
            modulus=1<<width
            calls=0
            def equation(z,t):
                nonlocal calls
                calls+=1
                a,b=(z-expected[0])%modulus,(t-expected[1])%modulus
                def poly(terms):
                    return sum(c*pow(a,i,modulus)*pow(b,j,modulus) for (i,j),c in terms)%modulus
                return ((a+a*(a+1)*b*poly(r1))%modulus,
                        (b+b*(b+1)*a*poly(r2))%modulus)
            actual=lift(equation,width)  # No coefficients, R1/R2, or expected root passed.
            assert actual==tuple(expected)
            assert calls==width+1
            return calls
        small=[]
        for width in range(1,5):
            calls=sum(check(width,(x,y)) for x in range(1<<width) for y in range(1<<width))
            small.append(dict(width=width,roots=1<<(2*width),equation_calls=calls))
        large=[]
        for _ in range(16):
            expected=[rng.getrandbits(32),rng.getrandbits(32)]
            calls=check(32,expected)
            large.append(dict(expected=expected,recovered=expected,calls=calls))
        records.append(dict(degree_bound=candidate['degree_bound'],instance=candidate['instance'],small=small,large=large))
    result=dict(python=platform.python_version(),seed=SEED,cases=records,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        code_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['check.py','lift.py']})
    destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(cases=len(records),small_roots=sum(s['roots'] for r in records for s in r['small']),
                         large_roots=sum(len(r['large']) for r in records),
                         equation_calls=sum(s['equation_calls'] for r in records for s in r['small'])+
                                        sum(s['calls'] for r in records for s in r['large']))))

if __name__=='__main__': main()
