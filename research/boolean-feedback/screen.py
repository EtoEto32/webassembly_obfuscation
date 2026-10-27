"""Screen direct residual feedback without an invertible coordinate map.

This is a model-level correctness gate, not a new obfuscation claim.
"""
import itertools
import json
from pathlib import Path
import random
import sys
import time


def triangular(n):
    for tables in itertools.product(*(range(1<<(1<<i)) for i in range(n))):
        f=[sum(((tables[i]>>(s&((1<<i)-1)))&1)<<i for i in range(n)) for s in range(1<<n)]
        yield tables,f


def converges(h,target):
    worst=0
    for s in range(len(h)):
        seen=[]
        while s!=target:
            if s in seen:return False,seen+[s]
            seen.append(s);s=h[s]
        worst=max(worst,len(seen))
    return True,worst


def prefix(n,N):
    return all((N[e]&((e&-e)*2-1))==0 for e in range(1,1<<n)) and N[0]==0


def check(n,N,fs):
    bound=0
    for tables,f in fs:
        target=next(s for s in range(1<<n) if f[s]==s)
        h=[f[s]^N[s^f[s]] for s in range(1<<n)]
        ok,detail=converges(h,target)
        if not ok:return {'valid':False,'source_tables':tables,'source_map':f,'feedback_map':h,'target':target,'cycle_trace':detail}
        bound=max(bound,detail)
    return {'valid':True,'bound':bound}


def main(output):
    start=time.perf_counter();out=Path(output);out.mkdir(parents=True,exist_ok=False);result={}
    fs=list(triangular(2));rows=[]
    for tail in itertools.product(range(4),repeat=3):
        N=[0,*tail];r=check(2,N,fs);rows.append({'N':N,'prefix':prefix(2,N),**r})
    result['dimension2']={'feedbacks':64,'source_DAGs':len(fs),'all_records':rows,'universal_count':sum(r['valid'] for r in rows),'prefix_count':sum(r['prefix'] for r in rows),'classification_mismatches':[r for r in rows if r['valid']!=r['prefix']]}
    # Known nonlinear nilpotent map: a state with exactly one zero maps to
    # that zero's one-hot complement; all other states map to zero.
    N=[sum((1<<i) for i in range(3) if e==7^(1<<i)) for e in range(8)]
    result['nonlinear_nilpotent']={'N':N,'N_squared':[N[N[s]] for s in range(8)],'against_triangular_DAGs':check(3,N,list(triangular(3)))}
    rng=random.Random(20261023);fs3=list(triangular(3));rows3=[]
    for i in range(10000):
        N=[0]+[rng.randrange(8) for _ in range(7)]
        r=check(3,N,fs3);rows3.append({'N':N,'prefix':prefix(3,N),**r})
    result['dimension3_sample']={'feedbacks':len(rows3),'source_DAGs':len(fs3),'seed':20261023,'universal_count':sum(r['valid'] for r in rows3),'prefix_count':sum(r['prefix'] for r in rows3),'classification_mismatches':[r for r in rows3 if r['valid']!=r['prefix']],'sampled_not_exhaustive':True}
    (out/'dimension3-samples.json').write_text(json.dumps(rows3))
    result['elapsed_ms']=(time.perf_counter()-start)*1000;(out/'screen.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!='all_records'} if isinstance(v,dict) else v for k,v in result.items()},indent=2))

if __name__=='__main__':main(sys.argv[1])
