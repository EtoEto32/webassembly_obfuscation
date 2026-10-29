"""XOR-constraint reconstruction from public answers and a declared schema only."""
from collections import deque


def recover(answers,n,shift,offsets=(0,1)):
    if not 0<=n<=65536:raise ValueError('Private prefix size')
    stride=1<<shift;limit=65535-max(offsets)
    count=min(limit//stride+1,max(0,(n-min(offsets)+stride-1)//stride))
    if len(answers)!=count:raise ValueError('Incomplete answers')
    graph=[[] for _ in range(n+1)];anchor=n
    for i,value in enumerate(answers):
        if not 0<=value<=255:raise ValueError('Not a byte')
        u,v=[min(n,i*stride+o) for o in offsets]
        graph[u].append((v,value));graph[v].append((u,value))
    values=[None]*(n+1);components=[];free=[]
    for root in [anchor]+list(range(n)):
        if values[root] is not None:continue
        values[root]=0;q=deque([root]);component=[]
        while q:
            u=q.popleft();component.append(u)
            for v,w in graph[u]:
                inferred=values[u]^w
                if values[v] is None:values[v]=inferred;q.append(v)
                elif values[v]!=inferred:raise ValueError('Inconsistent public answers')
        components.append(component)
        if root!=anchor:free.append(component)
    alt=values[:n]
    for component in free:
        for u in component:alt[u]^=0xa5
    return {'representative':values[:n],'alternative':alt,'free_components':len(free),
            'rank_in_bytes':n-len(free),'preimage_bits':8*len(free),'queries':len(answers)}
