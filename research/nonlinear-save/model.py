"""Exact finite-state save synthesis from two coarsening partition chains."""
import itertools, json, random, sys
from pathlib import Path

def copy(x,op,n):
    dst,src,size=op;old=x
    for k in range(size):
        x=(x&~(1<<(dst+k)))|(((old>>(src+k))&1)<<(dst+k))
    return x

def plan(n,ops,encoding):
    size=1<<n
    if sorted(encoding)!=list(range(size)):raise ValueError('encoding not bijective')
    inverse=[encoding.index(i) for i in range(size)];side=[list(range(size))];target=[list(range(size))]
    for op in ops:
        dst,src,length=op
        if min(dst,src)<0 or length<=0 or max(dst,src)+length>n:raise ValueError('copy outside state')
        side.append([copy(x,op,n) for x in side[-1]])
        target.append([encoding[copy(inverse[x],op,n)] for x in target[-1]])
    # Append a common terminal partition so every pair has a merge time.
    s=side+[[0]*size];t=target+[[0]*size]
    def split(vs):
        if len(vs)==1:return {vs[0]:0},[vs[0]],1
        hs=next(j for j,row in enumerate(s) if len({row[v] for v in vs})==1)
        ht=next(j for j,row in enumerate(t) if len({row[v] for v in vs})==1)
        join=hs<ht;row=t[ht-1] if join else s[hs-1];groups={}
        for v in vs:groups.setdefault(row[v],[]).append(v)
        if len(groups)<2:raise AssertionError('nondecreasing recursion')
        colors={};clique=[];count=0
        for group in groups.values():
            cs,cl,k=split(group)
            colors.update({v:c+(count if join else 0) for v,c in cs.items()})
            if join:clique+=cl;count+=k
            else:
                if k>count:clique=cl
                count=max(count,k)
        return colors,clique,count
    colors,clique,k=split(list(range(size)));colors=[colors[v] for v in range(size)]
    edges=[(a,b) for a in range(size) for b in range(a+1,size) if any(ss[a]==ss[b] and tt[a]!=tt[b] for ss,tt in zip(side,target))]
    edge_set=set(edges)
    assert all(colors[a]!=colors[b] for a,b in edges)
    assert len(clique)==k and all(tuple(sorted((a,b))) in edge_set for a,b in itertools.combinations(clique,2))
    return {'n':n,'ops':ops,'encoding':encoding,'inverse':inverse,'side':side,'target':target,'colors':colors,'color_count':k,'color_bits':(k-1).bit_length(),'clique':clique,'edges':edges}

def subspaces(n):
    """Enumerate GF(2)^n subspaces by adding one independent vector."""
    seen={frozenset([0])};front=list(seen)
    while front:
        space=front.pop()
        for v in range(1,1<<n):
            if v in space:continue
            ext=frozenset(set(space)|{a^v for a in space})
            if ext not in seen:seen.add(ext);front.append(ext)
    return sorted(seen,key=lambda x:(-len(x),sorted(x)))

def linear_save(info,spaces=None):
    n=info['n'];differences={a^b for a,b in info['edges']}
    kernel=next(s for s in (spaces if spaces is not None else subspaces(n)) if not (s&differences))
    reps={};colors=[]
    for x in range(1<<n):
        representative=min(x^v for v in kernel)
        if representative not in reps:reps[representative]=len(reps)
        colors.append(reps[representative])
    assert all(colors[a^b]==(colors[a]^colors[b]) for a in range(1<<n) for b in range(1<<n))
    return {'kernel':sorted(kernel),'colors':colors,'color_count':len(reps),'color_bits':(len(reps)-1).bit_length()}

def main(dest):
    out=Path(dest);out.mkdir(parents=True,exist_ok=False);rng=random.Random(213091);spaces=subspaces(4);rows=[];chosen=[]
    patterns=[[(1,0,1),(2,1,2)],[(0,1,2),(2,0,2)],[(3,0,1),(1,2,1),(2,0,1)]]
    for opid,ops in enumerate(patterns):
        for seed in range(200):
            e=list(range(16));random.Random(213100+seed+opid*200).shuffle(e)
            info=plan(4,ops,e);linear=linear_save(info,spaces)
            row={'pattern':opid,'seed':213100+seed+opid*200,'color_bits':info['color_bits'],'linear_bits':linear['color_bits'],'color_count':info['color_count']};rows.append(row)
            if info['color_bits']<linear['color_bits'] and not any(c['pattern']==opid for c in chosen):chosen.append({**row,'info':info,'linear':linear})
    (out/'screen.json').write_text(json.dumps({'cases':len(rows),'subspaces':len(spaces),'rows':rows,'chosen':chosen},indent=2),encoding='utf-8')
    print(json.dumps({'cases':len(rows),'better_than_linear':sum(r['color_bits']<r['linear_bits'] for r in rows),'chosen':[{k:v for k,v in r.items() if k not in ('info','linear')} for r in chosen]}))
if __name__=='__main__':main(sys.argv[1])
