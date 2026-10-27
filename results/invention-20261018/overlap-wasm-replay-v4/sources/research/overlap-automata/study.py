"""Model-only scaling and independent semantic checks; not Wasm runtime data."""
from collections import deque
from dataclasses import asdict
import argparse
import itertools
import json
from pathlib import Path
import random
import time
import prototype as p
from run import save,models


def intersections(d):
    nonempty=[]
    for x in range(d.n):
        for y in range(x+1,d.n):
            todo=deque([(x,y)]);seen=set(todo);found=False
            while todo:
                a,b=todo.popleft()
                if (d.final>>a)&(d.final>>b)&1:found=True;break
                for c in (0,1):
                    pair=(d.trans[a][c],d.trans[b][c])
                    if pair not in seen:seen.add(pair);todo.append(pair)
            if found:nonempty.append([x,y])
    return nonempty


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    rng=random.Random(20261018);checks=[]
    for i in range(120):
        n=rng.randrange(1,7);original=p.m.NFA([[rng.randrange(1<<n) for _ in (0,1)] for _ in range(n)],rng.randrange(1,1<<n),rng.randrange(1<<n))
        reduced=p.m.simulation(original);da,ra=p.m.determinize(original);db,rb=p.m.determinize(reduced)
        equal,pairs=p.m.equivalent(da,db);assert equal
        checks.append(dict(case=i,states=n,reduced=reduced.n,equivalent=equal,pairs=pairs))
    save(out/'simulation-checks.json',checks)
    ds=models();ds['suffix01101011']=p.m.pattern([0,1,1,0,1,0,1,1]);ds['contains01101011']=p.m.pattern([0,1,1,0,1,0,1,1],True)
    ds['mod8']=p.m.DFA([[(q+1)%8,(q+2)%8] for q in range(8)],1)
    # Arbitrary reachable/minimal 8-state source, using a deterministic seed.
    for _ in range(10000):
        rows=[[rng.randrange(8) for _ in (0,1)] for _ in range(8)];f=rng.randrange(1,255)
        delta,final=p.s.canonical(list(map(list,zip(*rows))),f)
        if len(delta[0])==8:ds['random8']=p.m.DFA(list(map(list,zip(*delta))),final);break
    records=[];saved_models={};admissibility={}
    for name,d in ds.items():
        admissibility[name]=dict(states=d.n,nonempty_residual_intersections=intersections(d))
        for k in (3,5):
            guard=p.m.universal(k);ud,ur=p.m.determinize(guard);assert p.m.minimize(ud).n==1 and ud.final==(1<<ud.n)-1
            base=p.m.trim(p.m.lift(d,guard))
            for mode in ('lift','random','overlap'):
                for seed in ([20261018] if mode=='lift' else [20261018,20261019]):
                    generation=dict(rounds=0,ms=0);n=base
                    if mode!='lift':n,generation=p.m.choose_merges(d,n,12,seed,mode)
                    cert=p.m.certificate(d,n);assert cert['valid'];attacks=[]
                    for method in ('subset','bisimulation','simulation','reverse'):
                        recovered,report=p.attack(n,method,10000)
                        if recovered is not None:
                            equivalent,pairs=p.m.equivalent(d,recovered);assert equivalent
                            report.update(equivalent=equivalent,check_pairs=pairs)
                        attacks.append(report)
                    if not admissibility[name]['nonempty_residual_intersections']:assert cert['overlap']==0
                    key=f'{name}.k{k}.{mode}.{seed}'
                    records.append(dict(key=key,name=name,guard=k,mode=mode,seed=seed,states=n.n,certificate=cert,generation=generation,attacks=attacks))
                    saved_models[key]=dict(dfa=asdict(d),nfa=asdict(n))
            print(json.dumps(dict(completed=name,guard=k,records=len(records))),flush=True)
    save(out/'admissibility.json',admissibility);save(out/'results.json',records);save(out/'models.json',saved_models)
    # A counterexample from an invalid identification must distinguish the two
    # actual model languages; correctness is not merely inferred from a score.
    d=ds['mod4'];n=p.m.trim(p.m.lift(d,p.m.universal(3)));bad=[]
    for i in range(n.n):
        for j in range(i+1,n.n):
            changed=p.m.trim(p.m.merge(n,i,j));c=p.m.certificate(d,changed)
            if not c['valid']:
                assert changed.accepts(c['word'])==1 and d.accepts(c['word'])==0
                bad.append(dict(pair=[i,j],word=c['word']))
    assert bad;save(out/'unsafe-merges.json',dict(checked=n.n*(n.n-1)//2,rejected=len(bad),witnesses=bad))
    print(json.dumps(dict(done=True,conditions=len(records),simulation_checks=len(checks))),flush=True)


if __name__=='__main__':main()
