"""Independent minimum-subspace search beyond copy-derived demands."""
import json
from pathlib import Path
import random
import sys
import prototype as p
from model import subspaces


def main(dest):
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False);rng=random.Random(20261023);spaces=subspaces(4);rows=[]
    for i in range(1000):
        b=p.base.encoding(4,i+20261023);dims=sorted([rng.randrange(5) for _ in range(4)],reverse=True)
        ps=[b[:d] for d in dims];ds=[[rng.randrange(16) for _ in range(rng.randrange(5))] for _ in dims]
        actual=len(p.saves(ps,ds))
        expected=next(len(v) for v in spaces if all(all(p.decoder(side+v)(d) is not None for d in demand) for side,demand in zip(ps,ds)))
        if actual!=expected:raise AssertionError((ps,ds,actual,expected))
        rows.append(dict(dimensions=dims,side=ps,demand=ds,minimum=expected,greedy=actual))
    p.q.save(out/'holdout.json',dict(instances=len(rows),subspaces=len(spaces),mismatches=0,rows=rows));print(len(rows),len(spaces))


if __name__=='__main__':main(sys.argv[1])
