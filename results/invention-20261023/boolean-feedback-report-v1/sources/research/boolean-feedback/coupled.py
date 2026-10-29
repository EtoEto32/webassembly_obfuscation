"""Connect local correctors through arbitrary, state-dependent mode selection."""
import argparse
import json
import random
import time
from shared import h
import prototype as base
import family

FAMILIES={2:[base.N2,[0,0,0,2]],3:[base.N3,[0,4,3,0,0,0,0,0]]}


def construct(n,f,nodes,mode='coupled',seed=20261023):
    if mode!='coupled':return base.construct(n,f,nodes,mode,seed)
    _,old=base.construct(n,f,nodes,'feedback',seed);maps=list(f);details=[];bound=0;d=len(f)
    for info in old['groups']:
        group=info['group'];k=len(group)
        if k==1:bound+=1;details.append(info);continue
        fam=FAMILIES[k];certificate=family.verify(k,fam);assert certificate['valid'];bound+=certificate['bound']
        # Bit-dependent choice may involve future and rotated current states.
        # It is a choice of corrector only, not an extra source operand.
        controls=[(group[-1]+1)%d,(group[-1]+3)%d]
        selector=h.add(h.var(n+controls[0],7),h.var(n+controls[1],19))
        err=[h.add(h.var(n+i),f[i]) for i in group]
        ca=[[h.sub(poly,err) for poly in base.anf(table,k)] for table in fam]
        for j,i in enumerate(group):maps[i]=h.add(f[i],h.add(ca[0][j],h.mul(selector,h.add(ca[0][j],ca[1][j]))))
        details.append({'group':group,'bound':certificate['bound'],'selector_words':controls,'selector_rotations':[7,19],'family':fam})
    if bound>24:raise ValueError('Evaluator round cap')
    perm=list(range(d-1));random.Random(seed).shuffle(perm);perm.append(d-1)
    env=[h.var(i) for i in range(n)]+[h.var(n+perm[i]) for i in range(d)];renamed=[None]*d
    for i,poly in enumerate(maps):renamed[perm[i]]=h.sub(poly,env)
    r={'n':n,'d':d,'depth':bound,'maps':[[list(m) for m in sorted(poly)] for poly in renamed]}
    return r,{'groups':details,'state_permutation':perm,'terms':sum(map(len,renamed)),'degree':max(len(m) for poly in renamed for m in poly),'bound':bound}


def transform(src,dest,mode='coupled'):
    start=time.perf_counter();n,f,depth,nodes=h.source(src);r,meta=construct(n,f,nodes,mode);h.save(h.render(r),dest)
    return {**meta,'n':n,'d':len(f),'elapsed_ms':1000*(time.perf_counter()-start),'memory_bytes':h.layout(r)[-1]*65536}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');q=ap.parse_args();print(json.dumps(transform(q.input,q.output),indent=2))
