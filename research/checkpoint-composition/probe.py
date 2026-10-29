"""Early rejection gate for quadratic iteration checkpoint elimination.

Recover every odd-leading quadratic formal root of Q=f compose f over Z/(2^w).
No source coefficients are an input to recover(). Not a general functional root solver.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import time


def mul(p,q,m):
    out=[0]*(len(p)+len(q)-1)
    for i,a in enumerate(p):
        for j,b in enumerate(q):out[i+j]=(out[i+j]+a*b)%m
    return out


def compose(p,q,m):
    out=[0]
    for a in reversed(p):
        out=mul(out,q,m);out[0]=(out[0]+a)%m
    while len(out)>1 and out[-1]==0:out.pop()
    return tuple(out)


def value(p,x,m):
    r=0
    for a in reversed(p):r=(r*x+a)%m
    return r


def recover(q,bits):
    if bits<3:raise ValueError('width >= 3 required')
    m=1<<bits;half=m>>1
    if len(q)!=5 or not(q[4]&1):return {'status':'unsupported_even_or_nonquartic','roots':[],'candidates':0}
    if q[3]&1:return {'status':'no_formal_root','roots':[],'candidates':0}
    # On odd residues, cubing is a bijection: inverse exponent modulo 2^(w-2).
    a=pow(q[4],pow(3,-1,1<<(bits-2)),m)
    inv=pow(a*a,-1,half)
    b0=(q[3]//2*inv)%half
    roots=[];tried=0
    for b in [b0,b0+half]:
        rem=(q[2]-a*b*b-a*b)%m
        if rem&1:continue
        c0=(rem//2*inv)%half
        for c in [c0,c0+half]:
            tried+=1;p=(c,b,a)
            if compose(p,p,m)==tuple(q):roots.append(p)
    return {'status':'recovered' if roots else 'no_formal_root','roots':roots,'candidates':tried}


def run(out):
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'probe.py')
    exhaustive=[]
    for bits in [3,4,5]:
        m=1<<bits;groups={}
        for a in range(1,m,2):
            for b in range(m):
                for c in range(m):
                    p=(c,b,a);q=compose(p,p,m);groups.setdefault(q,[]).append(p)
        missing=extra=0
        for q,truth in groups.items():
            actual=recover(q,bits)['roots']
            missing+=len(set(truth)-set(actual));extra+=len(set(actual)-set(truth))
        assert not missing and not extra
        exhaustive.append({'bits':bits,'source_quadratics':sum(map(len,groups.values())),
            'distinct_compositions':len(groups),'missing_roots':missing,'spurious_roots':extra,
            'root_multiplicities':dict(Counter(map(len,groups.values())))})
    rng=random.Random(20261018);m=1<<32;rows=[];failures=0;checks=0
    for i in range(4096):
        source=(rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32)|1)
        q=compose(source,source,m);r=recover(q,32)
        # Source is used only after the recovery function has returned.
        assert source in r['roots'] and r['candidates']<=4
        for root in r['roots']:
            assert compose(root,root,m)==q
            for x in [0,1,2,3,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]+[rng.getrandbits(32) for _ in range(24)]:
                checks+=1
                if value(root,value(root,x,m),m)!=value(source,value(source,x,m),m):failures+=1
        rows.append({'source':source,'composition':q,**r})
    samples=[]
    for _ in range(7):
        t=time.perf_counter_ns()
        for row in rows:recover(row['composition'],32)
        samples.append((time.perf_counter_ns()-t)/len(rows))
    controls=[recover((0,0,0,1,1),32),recover((0,0,0,0,2),32)]
    assert controls[0]['status']=='no_formal_root' and controls[1]['status'].startswith('unsupported')
    r={'width_exhaustion':exhaustive,'word_cases':len(rows),'two_step_value_comparisons':checks,
       'value_mismatches':failures,'max_candidates':max(x['candidates'] for x in rows),
       'root_multiplicities':dict(Counter(len(x['roots']) for x in rows)),
       'ns_per_recovery_batches':samples,'median_ns_per_recovery':statistics.median(samples),
       'controls':controls,'rows':rows,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'scope':'Formal polynomial coefficient equality. Equality as finite-ring functions can have additional roots.'}
    (out/'results.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k not in ['rows','ns_per_recovery_batches','code_sha256']}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();run(a.output)
