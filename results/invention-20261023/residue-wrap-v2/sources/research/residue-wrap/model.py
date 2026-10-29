import math
from pathlib import Path
import sys
import time
import prototype as p


def crt(a,b,m,n):return a+m*((b-a)%n*pow(m,-1,n)%n)


def main(dest):
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False);rows=[];total=0
    for width in range(2,9):
        size=1<<width;k=(width+1)//2;odd=(2**k+1,2**k+3);aligned=(size,odd[0])
        assert math.gcd(*odd)==math.gcd(*aligned)==1
        for mode,(m,n) in [('odd',odd),('aligned',aligned)]:
            errors={op:0 for op in ('add','sub','mul')};first={}
            for a in range(size):
                for b in range(size):
                    for op,fn in [('add',lambda x,y:x+y),('sub',lambda x,y:x-y),('mul',lambda x,y:x*y)]:
                        expected=fn(a,b)%size;aa=fn(a%m,b%m)%m;bb=fn(a%n,b%n)%n
                        actual=crt(aa,bb,m,n)%size;total+=1
                        if actual!=expected:
                            errors[op]+=1;first.setdefault(op,dict(a=a,b=b,actual=actual,expected=expected))
            if mode=='aligned' and any(errors.values()):raise AssertionError('aligned failed')
            rows.append(dict(width=width,mode=mode,moduli=[m,n],cases=3*size*size,errors=errors,witnesses=first))
    sys.path.insert(0,str(p.ROOT/'.tools/encoding-synthesis-python'));import z3 as z
    a,b=z.BitVecs('a b',64);lo=lambda x:z.Extract(31,0,x)
    formulas={'add':lo(a+b)==lo(a)+lo(b),'sub':lo(a-b)==lo(a)-lo(b),'mul':lo(a*b)==lo(a)*lo(b),
              'rem_word':lo(z.URem(a,z.BitVecVal(2**32,64)))==lo(a),'and_mask':lo(a & (2**32-1))==lo(a),
              'shift32':lo(a<<32)==0}
    proofs=[]
    for name,e in formulas.items():
        s=z.Solver();s.set(timeout=10000);s.add(z.Not(e));start=time.perf_counter();status=str(s.check())
        if status!='unsat':raise AssertionError((name,status))
        proofs.append(dict(name=name,status=status,ms=(time.perf_counter()-start)*1000))
    M=65537*65539
    witness=dict(a=0xffffffff,b=0xffffffff,expected=(2*0xffffffff)%2**32,actual=((2*0xffffffff)%M)%2**32,M=M)
    if witness['expected']==witness['actual']:raise AssertionError('bad witness')
    p.q.save(out/'model.json',dict(cases=total,rows=rows,word32_witness=witness,lemmas=proofs,z3=z.get_version_string()))
    print(total,witness)


if __name__=='__main__':main(sys.argv[1])
