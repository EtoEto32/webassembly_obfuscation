"""Check the history rule at small widths and arbitrary 32-bit masks."""
import itertools
import json
import random
import sys
import time
from pathlib import Path
import prototype as p


def check(seed,inputs,k,mask,w):
    s=p.schedule(k,mask,w);h=s['history'];past=[p.rot(seed,-a*k,w)&mask for a in range(h)];us=[0]*(h-1);y=seed
    for u in inputs:
        z=u&mask
        for a,m in enumerate(s['output_masks']):z^=p.rot(past[a],(a+1)*k,w)&m
        for j,m in enumerate(s['input_masks'][1:],1):z^=p.rot(us[j-1],j*k,w)&m
        y=p.rot(y,k,w)^u
        assert z==y&mask,(seed,inputs,k,mask,w)
        past=[z]+past[:-1]
        if us:us=[u]+us[:-1]


def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();counts=[]
    for w in range(1,5):
        count=0
        for k in range(w):
            for mask in range(1,1<<w):
                for seed,a,b in itertools.product(range(1<<w),repeat=3):
                    check(seed,[a,b],k,mask,w);count+=1
        counts.append(dict(width=w,sequences=count,steps=2*count))
    rng=random.Random(21102194);cases=[]
    for _ in range(512):
        seed=rng.getrandbits(32);k=rng.randrange(32);mask=rng.getrandbits(32) or 1
        inputs=[rng.getrandbits(32) for _ in range(64)];check(seed,inputs,k,mask,32)
        cases.append(dict(seed=seed,rotation=k,mask=mask,inputs=inputs))
    p.q.save(out/'random-cases.json',cases)
    p.q.save(out/'summary.json',dict(exhaustive=counts,random_sequences=len(cases),random_steps=64*len(cases),mismatches=0,elapsed_s=time.perf_counter()-start))
    print(json.dumps(dict(exhaustive_sequences=sum(x['sequences'] for x in counts),random_sequences=len(cases),mismatches=0)))


if __name__=='__main__':main()
