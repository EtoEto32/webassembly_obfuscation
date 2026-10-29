"""Refuse side effects and malformed transition data; randomized model checks."""
import argparse
import json
from pathlib import Path
import random
import prototype as p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    base=[[1,0,0],[0,1,1]];results=[]
    for label,text,action in [
        ('source_store',p.s.plain([[r[c] for r in base]+[0]*14 for c in range(2)],2).replace('(block (loop','(i32.store8 (i32.const 0) (i32.const 7)) (block (loop'),'source'),
        ('recovery_store',p.table_wat(base,0).replace('(block (loop','(i32.store8 (i32.const 0) (i32.const 7)) (block (loop'),'recover'),
        ('wrong_public_address',p.table_wat(base,0).replace('(i32.add (local.get 0) (local.get 2))','(i32.sub (local.get 0) (local.get 2))'),'recover')]:
        binary=a.output/(label+'.wasm');p.compile_wat(text,binary)
        try:
            if action=='source':p.source(binary,a.output)
            else:p.extract(binary,a.output)
        except ValueError as e:results.append(dict(control=label,status='rejected',reason=str(e)))
        else:raise AssertionError('Unsafe input accepted: '+label)
    rng=random.Random(20261019);models=[]
    for n in range(1,17):
        for trial in range(8):
            rows=[[rng.randrange(n),rng.randrange(n),rng.randrange(2)] for _ in range(n)]
            original,_=p.quotient(rows)
            for k in (1,3,17):
                full,start=p.lift(rows,k,rng.randrange(2**32));small,stats=p.quotient(full,start);eq=p.equivalent(rows,small)
                assert eq['equivalent'] and len(small)==len(original)
                models.append(dict(n=n,k=k,states=len(small),**eq))
    report=dict(rejections=results,model_conditions=len(models),model_mismatches=0,models=models)
    (a.output/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='models'}))

if __name__=='__main__':main()
