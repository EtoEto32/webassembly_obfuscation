"""Independent integer evaluation of extracted expression ASTs; no Wasm run."""
import hashlib
import json
import random
from pathlib import Path
from test_integer_expression_analysis import evaluate
from analyze_integer_expressions import variables

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/countermeasures/expression-analysis/extracted-output-checks.json'


def main():
    rng=random.Random(20261010);checks=0;expressions=0;records=[]
    for directory in ['expression-analysis','cryptic-expression-transfer']:
        comparison=ROOT/'results/countermeasures'/directory/'comparison.json'
        report=json.loads(comparison.read_text(encoding='utf-8'))
        for row in report['records']:
            detail=ROOT/row['detail']
            matches=json.loads(detail.read_text(encoding='utf-8'))['matches']
            count=0
            for match in matches:
                bits=match['bits'];mask=(1<<bits)-1;shift=match['shift'];e=match['expression']
                assert len(variables(e))==1
                values=[0,1,mask,1<<(bits-1),(1<<shift)-1,1<<shift]+[rng.getrandbits(bits) for _ in range(100)]
                for x in values:
                    assert evaluate(e,x,bits)==((x<<shift)&mask),(detail,match['last_line'],x)
                    checks+=1;count+=1
                expressions+=1
            records.append(dict(detail=row['detail'],detail_sha256=hashlib.sha256(detail.read_bytes()).hexdigest(),expressions=len(matches),integer_checks=count))
    OUT.write_text(json.dumps(dict(passed=True,expressions=expressions,integer_checks=checks,records=records,
                                  wasm_executed=False,scope='Finite independent integer checks of local expression ASTs, not full-module or dynamic-path validation.'),indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,expressions=expressions,integer_checks=checks)))


if __name__=='__main__':
    main()
