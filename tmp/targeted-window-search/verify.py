import json
from pathlib import Path

root=Path(__file__).resolve().parent
r=json.loads((root/'results.json').read_text())

def calc(tree,a,b):
    if isinstance(tree,str): return dict(a=a,b=b,zero=0,one=1)[tree]
    op,left,right=tree
    x,y=calc(left,a,b),calc(right,a,b)
    if op=='add':value=x+y
    elif op=='sub':value=x-y
    elif op=='mul':value=x*y
    elif op=='xor':value=x^y
    else:raise ValueError(op)
    return value%8

checks=0
for case in r['cases']:
    for candidate in case['all_candidates']:
        for i,(a,b) in enumerate(r['states']):
            value=calc(candidate['tree'],a,b)
            assert value==candidate['signature'][i]==calc(case['source'],a,b)
            checks+=1
out=dict(checks=checks,mismatches=0,scope='Independent scalar tree evaluator; all 64 inputs for each selected profile')
(root/'verification.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(out)
