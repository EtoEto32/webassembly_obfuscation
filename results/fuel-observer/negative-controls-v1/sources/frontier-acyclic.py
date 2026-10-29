"""Weighted acyclic control graph for flattened, structured Core Wasm.

Does not solve feasibility of correlated predicates. Loops are rejected.
"""
def analyze(body,n,expr_cost,marker_arity):
    nodes=[{'cost':0,'edges':[],'event':None,'ast':None}]
    def node(cost,edges,event=None,ast=None):
        i=len(nodes);nodes.append({'cost':cost,'edges':edges,'event':event,'ast':ast});return i
    def seq(xs,nxt,labels,depth=0):
        if depth>64:raise ValueError('control nesting limit')
        for x in reversed(xs):
            op=x[0]
            if op=='block':
                if any(not isinstance(v,list) or v[0] in ('result','param','type') for v in x[1:]):raise ValueError('only flattened void block')
                nxt=seq(x[1:],nxt,[nxt]+labels,depth+1)
            elif op=='if':
                if len(x) not in (3,4) or x[2][0]!='then' or (len(x)==4 and x[3][0]!='else'):raise ValueError('only flattened void if')
                yes=seq(x[2][1:],nxt,[nxt]+labels,depth+1)
                no=seq(x[3][1:] if len(x)==4 else [],nxt,[nxt]+labels,depth+1)
                nxt=node(1+expr_cost(x[1],n),[yes,no],ast=x)
            elif op in ('br','br_if'):
                if len(x)!=(2 if op=='br' else 3):raise ValueError('branch values unsupported')
                depth_index=int(x[1])
                if not 0<=depth_index<len(labels):raise ValueError('branch label')
                edges=[labels[depth_index]];cost=1
                if op=='br_if':edges.append(nxt);cost+=expr_cost(x[2],n)
                nxt=node(cost,edges,ast=x)
            elif op=='return':
                if len(x)!=2:raise ValueError('unfolded return unsupported')
                nxt=node(1+expr_cost(x[1],n),[0],ast=x)
            elif op=='call':
                if len(x)!=2+marker_arity or x[1]!='0' or x[2][0]!='i32.const':raise ValueError('marker contract')
                nxt=node(1+sum(expr_cost(v,n) for v in x[2:]),[nxt],int(x[2][1])&0xffffffff,x)
            elif op in ('local.set','drop'):
                if op=='local.set' and (len(x)!=3 or not 0<=int(x[1])<n):raise ValueError('local.set shape')
                if op=='drop' and len(x)!=2:raise ValueError('drop shape')
                nxt=node(1+expr_cost(x[-1],n),[nxt],ast=x)
            elif op=='nop' and len(x)==1:nxt=node(1,[nxt],ast=x)
            else:nxt=node(expr_cost(x,n),[nxt],ast=x)
        return nxt
    entry=seq(body,0,[0])
    words=[()]
    for i,x in enumerate(nodes[1:],1):
        if any(e>=i for e in x['edges']):raise ValueError('cyclic control graph')
        successors=[words[e] for e in x['edges']]
        if any(v!=successors[0] for v in successors):raise ValueError('branch public event words differ')
        word=successors[0]
        if x['event'] is not None:word=(x['event'],)+word
        if len(word)>256:raise ValueError('event count limit')
        words.append(word)
    word=words[entry];dist=[-1]*len(nodes);tail=[-1]*len(nodes);dist[entry]=tail[entry]=0
    prefix=[0]*(len(word)+1);segment=[0]*(len(word)+1);ranks={}
    for i in range(len(nodes)-1,0,-1):
        if dist[i]<0:continue
        x=nodes[i];d=dist[i]+x['cost'];s=tail[i]+x['cost']
        if x['event'] is not None:
            rank=len(word)-len(words[i]);prefix[rank]=max(prefix[rank],d);segment[rank]=max(segment[rank],s);s=0
            ranks[id(x['ast'])]=rank
        for e in x['edges']:dist[e]=max(dist[e],d);tail[e]=max(tail[e],s)
    prefix[-1]=dist[0];segment[-1]=tail[0]
    if max(prefix)>2**53-1:raise ValueError('cost bound')
    return {'events':list(word),'prefix':prefix,'segment':segment,'cfgNodes':len(nodes)},ranks
