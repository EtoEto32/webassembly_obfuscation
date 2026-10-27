"""Additional basis seeds and conservative-solver controls; model evidence."""
import argparse
import statistics
import time
from run import a,models,save


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output');args=ap.parse_args()
    records=[]
    for name,f in models().items():
        for seed in range(24):
            p,c=a.conjugate(f,a.basis(seed));trials=[]
            for method,attack in [('linear_preimage',a.observe_recover),('known_factor',a.factor_recover)]:
                start=time.perf_counter();recovered,report=attack(p,c)
                report.update(method=method,analysis_ms=(time.perf_counter()-start)*1000)
                if recovered is not None:assert recovered==f
                trials.append(report)
            assert any(r['status']=='success' for r in trials)
            records.append(dict(model=name,seed=seed,terms=sum(map(len,p)),trials=trials))
    # These systems intentionally fall outside the implemented recovery paths.
    x=[a.var(i) for i in range(5)]
    f=[a.add(a.add(a.mul(x[i],x[i]),a.mul(x[(i+1)%4],x[(i+2)%4])),x[4]) for i in range(4)]
    p,c=a.conjugate(f,a.basis(17));negative=[]
    for name,attack in [('linear_preimage',a.observe_recover),('known_factor',a.factor_recover)]:
        recovered,report=attack(p,c);assert recovered is None
        negative.append(dict(case='outside_two_recovery_families',method=name,report=report))
    even=[a.scale(x[i],2) for i in range(4)]
    solution,report=a.preimage(even,even[0]);assert solution is None
    assert a.dot([1,0,0,0],even)==even[0]
    negative.append(dict(case='known_solution_but_nonunit_pivots',report=report,known_solution=[1,0,0,0]))
    null=a.scale(a.add(a.mul(x[0],x[0]),a.scale(x[0],-1)),1<<31)
    assert null
    from run import value
    assert all(value(null,[i])==0 for i in range(2048))
    negative.append(dict(case='formal_nonzero_null_polynomial',checked_values=2048,
                         explanation='2**31*x*(x-1) is zero as a function modulo 2**32; x*(x-1) is even'))
    save(args.output,dict(scope='algebra models, not additional Wasm binaries',records=records,negative_controls=negative))
    print(dict(model_conditions=len(records),recovered=sum(any(t['status']=='success' for t in r['trials']) for r in records),negative_controls=len(negative)))


if __name__=='__main__':main()
