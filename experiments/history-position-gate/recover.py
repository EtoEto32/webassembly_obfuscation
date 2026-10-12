"""Receive only anonymous aligned traces; return a unique 24-lane copy chain."""
def recover(training, length=24):
    if len(training)<3 or any(len(r)!=len(training[0]) for r in training):
        raise ValueError('invalid trace shape')
    columns=len(training[0])
    edges=[(a,b) for a in range(columns) for b in range(columns) if a!=b
           and all(training[t][a]==training[t+1][b] for t in range(len(training)-1))]
    successor={i:[] for i in range(columns)}
    predecessor={i:[] for i in range(columns)}
    for a,b in edges:
        successor[a].append(b);predecessor[b].append(a)
    candidates=[]
    for head in range(columns):
        if predecessor[head]: continue
        chain=[head]
        while len(successor[chain[-1]])==1:
            nxt=successor[chain[-1]][0]
            if nxt in chain or len(predecessor[nxt])!=1: break
            chain.append(nxt)
        if len(chain)==length and not successor[chain[-1]]:
            candidates.append(chain)
    if len(candidates)!=1:
        raise ValueError(f'expected one chain, found {len(candidates)}')
    return {'order':candidates[0],'edges':edges,'training_rows':len(training)}
