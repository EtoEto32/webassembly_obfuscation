import json
from pathlib import Path
import sys
import time
import prototype as p


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);t=time.perf_counter();rows=[];pairs=0
    for w in range(2,6):
        mod=1<<w;mask=mod-1
        for k in range(mod):
            d=p.erased(k,w);accepted=[]
            for c in range(mod):
                expected=(c % (1<<(w-d)))==0
                # All states of a two-cell array, every shift c and every k.
                # Delta zero suffices for this affine closure test: adding an
                # equal delta to the updated coordinate cancels in the comparison.
                okay=True
                for x in range(mod):
                    for y in range(mod):
                        left=(k*x-y)&mask;right=(k*((x+c)&mask)-((y+c)&mask))&mask
                        same=left==right;pairs+=1
                        if same!=expected:raise AssertionError((w,k,c,x,y,same,expected))
                        okay=okay and same
                if okay:accepted.append(c)
            if len(accepted)!=(1<<d):raise AssertionError('kernel size')
            rows.append(dict(width=w,k=k,d=d,valid_shifts=accepted))
    sys.path.insert(0,str(p.ROOT/'.tools/encoding-synthesis-python'));import z3
    proofs=[]
    for k in (0,1,3,257,65537,0xffffffff):
        x,y,c=z3.BitVecs('x y c',32);d=p.erased(k);low=(1<<(32-d))-1
        s=z3.Solver();s.set(timeout=10000);s.add(c&low==0,(k*x-y)!=(k*(x+c)-(y+c)))
        status=str(s.check());proofs.append(dict(k=k,d=d,status=status))
        if status!='unsat':raise AssertionError(proofs[-1])
    # All 8-bit a,b,m. Equality follows from a relational condition, not
    # exclusively from canonical masks. Either allowed profile is a normal form.
    total=0;valid=0
    for m in range(256):
        sign=255 if m&128 else 0;bad=m^sign
        for a in range(256):
            for b in range(256):
                bits=(a&m)|(b&(~m&255));lane=a if m&128 else b
                cond=((a^b)&bad)==0
                if (bits==lane)!=cond:raise AssertionError('laneselect equivalence')
                total+=1;valid+=cond
    p.q.save(out/'model.json',dict(closure_pairs=pairs,rows=rows,smt=proofs,laneselect=dict(tuples=total,equal_results=valid,canonical_mask_tuples=2*256*256),seconds=time.perf_counter()-t))
    print(json.dumps(dict(closure_pairs=pairs,smt=proofs,laneselect_equal=valid,seconds=time.perf_counter()-t)),flush=True)


if __name__=='__main__':main(sys.argv[1])
