"""Non-mining integer checks of the read-only analysis; no Wasm execution."""
import json
import random
from pathlib import Path
from analyze_integer_expressions import shift_identity, extract

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/countermeasures/expression-analysis'


def evaluate(e, x, bits):
    mask=(1<<bits)-1
    if e[0]=='var':
        return x
    if e[0]=='const':
        return e[1]&mask
    a,b=evaluate(e[1],x,bits),evaluate(e[2],x,bits)
    return {'add':lambda:a+b,'sub':lambda:a-b,'mul':lambda:a*b,
            'and':lambda:a&b,'or':lambda:a|b,'xor':lambda:a^b,
            'shl':lambda:a<<(b&(bits-1))}[e[0]]()&mask


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    checks=0;identities=0;rng=random.Random(20261010)
    x=('var','input')
    for bits in [8,32,64]:
        for shift in range(1,bits):
            c=('const',1<<shift)
            # Formula uses Boolean masking and arithmetic multiplication; this
            # generator is independent of local identifiers in the real artifact.
            e=('add',('mul',('and',x,('xor',c,('const',-1))),('and',('xor',x,('const',-1)),c)),
                     ('mul',('or',x,c),('and',x,c)))
            assert shift_identity(e,bits)==shift
            identities+=1
            values=list(range(256)) if bits==8 else [0,1,(1<<bits)-1,1<<(bits-1),(1<<shift)-1,1<<shift]+[rng.getrandbits(bits) for _ in range(100)]
            for value in values:
                assert evaluate(e,value,bits)==((value<<shift)&((1<<bits)-1))
                checks+=1
            assert shift_identity(('add',e,('const',1)),bits) is None
    # Mechanism-development fixture: selected real expression, renamed locals
    # and function names. This is a metamorphic check, not independent data.
    fixture=(ROOT/'results/runtime-mining/cross-dataset/proof-of-theft/xmr-core-substitution-reviewed.wat.txt').read_text(encoding='utf-8')
    body=fixture.split('VARIANT f111 lines 781--828\n',1)[1]
    import re
    body=re.sub(r'\$l(\d+)',lambda m:'$renamed'+m[1],body)
    text='  (func $test\n'+body+'  )\n'
    matches,_=extract(text)
    assert any(m['shift']==4 and m['output_local']=='$renamed222' for m in matches)
    reference=fixture.split('REFERENCE f111 lines 781--786\n',1)[1].split('VARIANT f111 lines 781--828\n',1)[0]
    reference_matches,_=extract('  (func $reference\n'+reference+'  )\n',minimum_nodes=3)
    assert reference_matches[-1]['shift']==4
    # A trapping division inserted before the final add must break propagation.
    broken=text.replace('            i32.add\n','            i32.div_u\n            i32.add\n')
    assert not any(m['output_local']=='$renamed222' for m in extract(broken)[0])
    result=dict(passed=True,identities=identities,finite_integer_checks=checks,
                renamed_real_fixture=True,reviewed_reference_correspondence=True,division_barrier=True,
                scope='Independent integer evaluator and bounded symbolic identities; finite checks are not whole-module proofs.',
                wasm_executed=False,mining_executed=False)
    (OUT/'tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':
    main()
