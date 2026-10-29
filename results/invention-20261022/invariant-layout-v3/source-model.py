import argparse,itertools,json
from pathlib import Path
import prototype as p

def run(output):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    cases=0;bad=0;first=None
    # Small-word h becomes low-two-bit identity; tests group/action and update laws.
    for bits in (1,2,3):
        for tup in itertools.product(range(1<<bits),repeat=4):
            x=list(tup);s=p.phase(x);y=p.rotate(x,s)
            assert p.phase(y)==s and p.rotate(y,-p.phase(y))==x
            for i in range(4):
                for new in range(1<<bits):
                    u=x.copy();u[i]=new;z=y.copy();j=(i+s)%4;old=z[j];z[j]=new
                    expected=p.rotate(u,p.phase(u));got=p.rotate(z,p.h(new)-p.h(old))
                    assert got==expected;cases+=1
                    if z!=expected:
                        bad+=1
                        if first is None:first=dict(x=x,i=i,new=new,without_repair=z,expected=expected)
    result=dict(update_cases=cases,bad_counterexamples=bad,first=first,scope='Exhaustive 1/2/3-bit values in four words; not full i32 implementation proof.')
    p.q.save(out/'model.json',result);print(json.dumps(result))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');run(ap.parse_args().output)
