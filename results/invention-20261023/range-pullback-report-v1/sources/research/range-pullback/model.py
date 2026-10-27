import itertools
import json
from pathlib import Path
import sys
import time


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();checks=0;rows=[]
    for n in range(1,9):
        ops=[(d,s,l) for l in range(n+1) for d,s in itertools.product(range(n-l+1),repeat=2)]
        local=0
        for first,second in itertools.product(ops,repeat=2):
            mem=list(range(n))
            for d,s,l in (first,second):mem[d:d+l]=mem[s:s+l]
            for q in range(n):
                address=q
                for d,s,l in (second,first):
                    if d<=address<d+l:address=s+address-d
                if mem[q]!=address:raise AssertionError((n,first,second,q))
                local+=1
        checks+=local;rows.append(dict(n=n,copy_operations=len(ops),checks=local))
    result=dict(symbolic_origin_checks=checks,mismatches=0,seconds=time.perf_counter()-start,rows=rows)
    (out/'model.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':main(sys.argv[1])
