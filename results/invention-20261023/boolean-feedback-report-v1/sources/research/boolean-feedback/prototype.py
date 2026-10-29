import argparse
import json
from pathlib import Path
import random
import time
from shared import h
import screen

# Selected before Wasm attack measurement: non-prefix, bounded by 3/4 rounds.
N2=[0,0,1,2]
N3=[0,2,3,0,0,2,0,0]


def anf(table,k):
    out=[]
    for bit in range(k):
        a=[(v>>bit)&1 for v in table]
        for j in range(k):
            for mask in range(1<<k):
                if mask>>j&1:a[mask]^=a[mask^(1<<j)]
        out.append({tuple(32*j for j in range(k) if mask>>j&1) for mask,v in enumerate(a) if v})
    return out


def construct(n,f,nodes,mode='feedback',seed=20261023):
    groups=[];pending=[]
    def flush():
        if pending:groups.append(list(pending));pending.clear()
    for i,node in enumerate(nodes):
        if node[0]=='rot':flush();groups.append([i])
        else:
            pending.append(i)
            if len(pending)==3:flush()
    flush();maps=list(f);bound=0;choices=[]
    for group in groups:
        k=len(group)
        if mode=='pipeline' or k==1:bound+=k;choices.append({'group':group,'bound':k,'N':[0]*(1<<k)});continue
        table=N2 if k==2 else N3;check=screen.check(k,table,list(screen.triangular(k)));assert check['valid']
        err=[h.add(h.var(n+i),f[i]) for i in group];nf=anf(table,k)
        for j,i in enumerate(group):maps[i]=h.add(f[i],h.sub(nf[j],err))
        bound+=check['bound'];choices.append({'group':group,'bound':check['bound'],'N':table})
    if mode=='pipeline':
        depths=[]
        for poly in f:depths.append(1+max([depths[v//32-n] for m in poly for v in m if v//32>=n]+[0]))
        bound=max(depths)
    if bound>24:raise ValueError('Current evaluator allows at most 24 rounds')
    # Renaming has zero runtime cost. Keep the exported output at the last slot.
    perm=list(range(len(f)-1));random.Random(seed).shuffle(perm);perm.append(len(f)-1)
    ren=[h.var(i) for i in range(n)]+[h.var(n+perm[i]) for i in range(len(f))];renamed=[None]*len(f)
    for i,poly in enumerate(maps):renamed[perm[i]]=h.sub(poly,ren)
    r={'n':n,'d':len(f),'depth':bound,'maps':[[list(m) for m in sorted(poly)] for poly in renamed]}
    return r,{'groups':choices,'state_permutation':perm,'terms':sum(map(len,renamed)),'degree':max(len(m) for poly in renamed for m in poly),'bound':bound}


def transform(src,dest,mode='feedback'):
    start=time.perf_counter();n,f,depth,nodes=h.source(src);r,meta=construct(n,f,nodes,mode);h.save(h.render(r),dest)
    return {**meta,'n':n,'d':len(f),'elapsed_ms':1000*(time.perf_counter()-start),'memory_bytes':h.layout(r)[-1]*65536}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--mode',choices=['pipeline','feedback'],default='feedback');q=ap.parse_args();print(json.dumps(transform(q.input,q.output,q.mode),indent=2))
