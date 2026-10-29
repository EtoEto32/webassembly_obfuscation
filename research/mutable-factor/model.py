import itertools
from pathlib import Path
import sys
import time
import prototype as p


def update(A,B,u,v,w,bad=False):
    a,b=A[u],A[w];t=B[b];A=A[:];B=B[:];A[u]=b;A[w]=a
    if bad:B[b]=v;B[a]=t
    else:B[a]=t;B[b]=v
    return A,B


def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();checks=0;bad=None
    for n in range(1,5):
        for perm in itertools.permutations(range(n)):
            A=list(perm)
            for values in itertools.product(range(n),repeat=n):
                B=list(values);N=[B[a] for a in A]
                for u,v,w in itertools.product(range(n),repeat=3):
                    expected=N[:];expected[u]=v;C,D=update(A,B,u,v,w)
                    if [D[a] for a in C]!=expected:raise AssertionError('model')
                    checks+=n
                    if bad is None:
                        C,D=update(A,B,u,v,w,True)
                        if [D[a] for a in C]!=expected:bad=dict(A=A,B=B,u=u,v=v,w=w,expected=expected,actual=[D[a] for a in C])
    sys.path.insert(0,str(p.ROOT/'.tools/encoding-synthesis-python'))
    import z3 as z
    I=z.BitVecSort(32);A=z.Array('A',I,I);B=z.Array('B',I,I);u,v,w,j=z.BitVecs('u v w j',32)
    a,b=A[u],A[w];C=z.Store(z.Store(A,u,b),w,a);D=z.Store(z.Store(B,a,B[b]),b,v)
    target=z.If(j==u,v,B[A[j]])
    injective=z.And(z.Or(u==w,a!=b),z.Or(j==u,A[j]!=a),z.Or(j==w,A[j]!=b))
    solver=z.Solver();solver.set(timeout=10000);solver.add(injective,D[C[j]]!=target);proof=str(solver.check())
    if proof!='unsat':raise AssertionError('SMT proof')
    solver=z.Solver();solver.add(D[C[j]]!=target);without=str(solver.check())
    if without!='sat':raise AssertionError('noninjective counterexample')
    witness=str(solver.model())
    p.q.save(out/'model.json',dict(origin_checks=checks,mismatches=0,seconds=time.perf_counter()-start,bad_order_witness=bad,word32_one_update=proof,without_injectivity=without,witness=witness,z3=z.get_version_string()))
    print(checks,proof,without)


if __name__=='__main__':main(sys.argv[1])
