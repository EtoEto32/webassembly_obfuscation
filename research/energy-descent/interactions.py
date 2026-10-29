# -*- coding: utf-8 -*-
"""Signed interaction revision with a source-independent recovery certificate."""
import argparse
import importlib.util
import json
from pathlib import Path
import random
import time
import relaxed as r

spec=importlib.util.spec_from_file_location('interaction_screen',r.p.HERE/'interactions-screen.py')
screen=importlib.util.module_from_spec(spec);spec.loader.exec_module(screen)

def build(I,gates,weights,interactions,gauge=True):
    n=len(gates);rng=random.Random(20261022);order=list(range(n));flips=[0]*n
    if gauge:rng.shuffle(order);flips=[rng.randrange(2) for _ in range(n)]
    def var(a):
        if a[0]=='input':return {1<<a[1]:1}
        i=a[1];v={1<<(I+order[i]):1}
        return r.p.plus({0:1},r.p.scale(v,-1)) if flips[i] else v
    errors=[]
    for i,(op,a,b) in enumerate(gates):
        z=var(['gate',i]);f=r.p.boolean(op,var(a),var(b))
        errors.append(r.p.plus(z,f,r.p.scale(r.p.product(z,f),-2)))
    E={}
    for w,e in zip(weights,errors):E=r.p.plus(E,r.p.scale(e,w))
    for i,j,c in interactions:E=r.p.plus(E,r.p.scale(r.p.product(errors[i],errors[j]),c))
    if sum(abs(c) for c in E.values())>=1<<62:raise ValueError('i64 coefficient bound')
    return {'inputs':I,'n':n,'output':order[-1],'flip':flips[-1],'terms':sorted(E.items())}

def public_certificate(record):
    """Check the evaluator's assumptions using aggregate coefficients alone.

    Existence of a zero for every x is supplied separately by exact elimination
    to the identically-zero residual. Here check nonnegativity, absence of bad
    local minima, and uniqueness of the observed output among zero states.
    """
    start=time.perf_counter();I,n=record['inputs'],record['n'];z3=r.z3
    x=z3.Bools(' '.join('x%d'%i for i in range(I)))
    z=z3.Bools(' '.join('z%d'%i for i in range(n)))
    t=z3.Bools(' '.join('t%d'%i for i in range(n)))
    def energy(state):
        bits=x+state
        return z3.Sum([z3.If(z3.And(*[b for k,b in enumerate(bits) if mask>>k&1]),c,0) for mask,c in record['terms']])
    E=energy(z);neighbors=[energy([z3.Not(a) if k==j else a for k,a in enumerate(z)]) for j in range(n)]
    queries={'negative_energy':E<0,'false_local_minimum':z3.And(E>0,*[a>=E for a in neighbors]),
             'ambiguous_zero_output':z3.And(E==0,energy(t)==0,z[record['output']]!=t[record['output']])}
    rows={}
    for label,q in queries.items():
        s=z3.Solver();s.set(timeout=15000);s.add(q);status=s.check();row={'status':str(status)}
        if status==z3.sat:row['counterexample']=str(s.model())
        elif status==z3.unknown:row['reason']=s.reason_unknown()
        rows[label]=row
    return {'checks':rows,'accepted':all(a['status']=='unsat' for a in rows.values()),'milliseconds':(time.perf_counter()-start)*1000}

def transform(src,out,robust_selectors=False):
    start=time.perf_counter();I,gates=r.p.source(src)
    if I+len(gates)>8 or len(gates)>6:raise ValueError('Finite synthesis screen cap: I+n <= 8 and n <= 6')
    syn=screen.synthesize(I,gates,robust_selectors=robust_selectors)
    if syn['status']!='sat':raise ValueError(json.dumps({k:v for k,v in syn.items() if k!='smt2'}))
    record=build(I,gates,syn['weights'],syn['interactions']);cert=public_certificate(record)
    if not cert['accepted']:raise ValueError(json.dumps(cert))
    r.p.save(r.render(record),out)
    return {'record':record,'synthesis':syn,'public_certificate':cert,'milliseconds':(time.perf_counter()-start)*1000}

def recover(src,out):
    start=time.perf_counter();record=r.read_family(src,out);cert=public_certificate(record)
    if not cert['accepted']:raise ValueError('Public energy certificate rejected: '+json.dumps(cert))
    model=r.eliminate(record);r.p.save(r.p.recovered_wat(model),out)
    return {'record':record,'model':model,'public_certificate':cert,'family_checked':True,'milliseconds':(time.perf_counter()-start)*1000}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['transform','recover']);ap.add_argument('source');ap.add_argument('output');ap.add_argument('--robust-selectors',action='store_true');a=ap.parse_args()
    print(json.dumps(transform(a.source,a.output,a.robust_selectors) if a.action=='transform' else recover(a.source,a.output),indent=2))
