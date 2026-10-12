"""Consumes coefficients only; no original states or transition history."""
import json
import sys
import time
from pathlib import Path


def recover(coeff, width, limit):
    X,Y,P,Q,R = coeff
    calls = 0
    exhausted = False
    def visit(a,b,k):
        nonlocal calls, exhausted
        if k == width:
            m = (1<<width)-1
            return (a,b,(X-a)&m,(Y-b)&m)
        bit = 1<<k
        mask = (bit<<1)-1
        for da,db in ((0,0),(0,bit),(bit,0),(bit,bit)):
            if calls >= limit:
                exhausted = True
                return None
            aa,bb = a+da,b+db
            cc,dd = (X-aa)&mask,(Y-bb)&mask
            calls += 1
            if ((aa*cc-P)&mask) or ((bb*dd-Q)&mask) or ((aa*dd+cc*bb-R)&mask):
                continue
            result = visit(aa,bb,k+1)
            if result is not None or exhausted:
                return result
        return None
    result = visit(0,0,0)
    return result, calls, 'success' if result is not None else ('budget' if exhausted else 'no-solution')


if __name__ == '__main__':
    source,target = map(Path,sys.argv[1:3])
    if target.exists():
        raise SystemExit('Preserve results.')
    observations = json.loads(source.read_text())
    with target.open('w',encoding='utf-8') as out:
        for i,record in enumerate(observations):
            start=time.perf_counter()
            result,calls,status = recover(record['coeff'],record['width'],100000)
            out.write(json.dumps(dict(id=record['id'],status=status,calls=calls,
                recovered=result,seconds=time.perf_counter()-start))+'\n')
            if i%256 == 0:
                out.flush()
                print(f'{i}/{len(observations)} observations processed',flush=True)
