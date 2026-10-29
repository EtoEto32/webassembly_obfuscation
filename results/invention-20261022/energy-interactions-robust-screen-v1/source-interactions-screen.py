# -*- coding: utf-8 -*-
"""Finite synthesis screen for signed interactions between violation bits.

Revision 3 of energy-descent. No independent invention claim.
All Boolean states of each small fixture are constraints, not sampled inputs.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import time
import relaxed as r


def features(errors,pairs):return errors+[errors[i]*errors[j] for i,j in pairs]
def dot(coeff,values):return r.z3.Sum([c*v for c,v in zip(coeff,values) if v])

def fixtures():
    x=lambda i:['input',i];g=lambda i:['gate',i]
    return {
        'fork':(2,[['xor',x(0),x(1)],['and',g(0),x(0)],['or',g(0),x(1)],['xor',g(1),g(2)]]),
        'chain':(2,[['xor',x(0),x(1)],['and',g(0),x(0)],['or',g(1),x(1)],['xor',g(2),x(0)]]),
        'ordered':(2,[['and',x(0),x(1)],['or',x(0),x(1)],['xor',g(0),g(1)],['and',g(2),x(0)]]),
    }


def synthesize(I,gates,bound=16,minimum_arity=3,timeout=30000,robust_selectors=False):
    start=time.perf_counter();n=len(gates);pairs=list(itertools.combinations(range(n),2));N=n+len(pairs)
    coeff=r.z3.Ints(' '.join('c%d'%i for i in range(N)));s=r.z3.Optimize();s.set(timeout=timeout)
    s.add(*[r.z3.And(c>=1,c<=bound) if k<n else r.z3.And(c>=-bound,c<=bound) for k,c in enumerate(coeff)])
    s.add(r.z3.Or(*[c<0 for c in coeff[n:]]))
    costs={}
    for x in range(1<<I):
        for z in range(1<<n):costs[x,z]=dot(coeff,features(r.errors(I,gates,x,z),pairs))
    # The source DAG has a unique all-zero error vector for every x.
    nonroots=0
    for (x,z),E in costs.items():
        if any(r.errors(I,gates,x,z)):
            s.add(E>0);s.add(r.z3.Or(*[costs[x,z^(1<<j)]<E for j in range(n)]));nonroots+=1
        else:s.add(E==0)
    deps={}
    for j in range(n):
        if robust_selectors:
            # A selector with <= 2 arguments exists iff each equivalence class
            # of those arguments has no contradictory strict sign requirements.
            # Zero differences are don't-cares, not artificially fixed to zero.
            coordinates=[k for k in range(I+n) if k!=I+j]
            for subset in itertools.combinations(coordinates,2):
                classes={a:[] for a in range(4)}
                for x in range(1<<I):
                    for z in range(1<<n):
                        if z>>j&1:continue
                        state=x|(z<<I);key=sum((state>>k&1)<<q for q,k in enumerate(subset))
                        classes[key].append(costs[x,z|(1<<j)]-costs[x,z])
                s.add(r.z3.Or(*[r.z3.And(r.z3.Or(*[d>0 for d in ds]),r.z3.Or(*[d<0 for d in ds])) for ds in classes.values()]))
            continue
        essential=[]
        for k in range(I+n):
            if k==I+j:continue
            differences=[]
            for x in range(1<<I):
                for z in range(1<<n):
                    if z>>j&1:continue
                    xx,zz=(x^(1<<k),z) if k<I else (x,z^(1<<(k-I)))
                    d=costs[x,z|(1<<j)]-costs[x,z]
                    dd=costs[xx,zz|(1<<j)]-costs[xx,zz]
                    differences.append(r.z3.Xor(d<0,dd<0))
            v=r.z3.Bool('dep_%d_%d'%(j,k));s.add(v==r.z3.Or(differences));essential.append(v)
        s.add(r.z3.PbGe([(v,1) for v in essential],minimum_arity));deps[j]=essential
    objective=s.minimize(r.z3.Sum([r.z3.If(c>=0,c,-c) for c in coeff]));status=s.check()
    result={'status':str(status),'inputs':I,'gates':gates,'bound':bound,'minimum_arity':minimum_arity,
            'nonroot_constraints':nonroots,'robust_selectors':robust_selectors,'milliseconds':(time.perf_counter()-start)*1000,
            'z3':r.z3.get_version_string(),'smt2':s.sexpr()+'\n(check-sat)\n'}
    if status==r.z3.sat:
        m=s.model();result.update(weights=[m.eval(c).as_long() for c in coeff[:n]],interactions=[[*pair,m.eval(c).as_long()] for pair,c in zip(pairs,coeff[n:])],objective_lower=str(s.lower(objective)))
    elif status==r.z3.unknown:result['reason']=s.reason_unknown()
    return result


def main(dst,robust=False):
    root=Path(dst);root.mkdir(parents=True,exist_ok=False);rows=[]
    for name,(I,gates) in fixtures().items():
        a=synthesize(I,gates,robust_selectors=robust);(root/(name+'.smt2')).write_text(a.pop('smt2'),encoding='utf8')
        rows.append({'name':name,**a});(root/(name+'.json')).write_text(json.dumps(a,indent=2),encoding='utf8')
        print(json.dumps({k:v for k,v in rows[-1].items() if k!='gates'}),flush=True)
    (root/'screen.json').write_text(json.dumps(rows,indent=2),encoding='utf8');shutil.copyfile(Path(__file__),root/'source-interactions-screen.py')
    for name in ('relaxed.py','prototype.py'):shutil.copyfile(r.p.HERE/name,root/('source-'+name))
    (root/'pins.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in root.iterdir() if x.is_file()},indent=2),encoding='utf8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');ap.add_argument('--robust-selectors',action='store_true');a=ap.parse_args();main(a.output,a.robust_selectors)
