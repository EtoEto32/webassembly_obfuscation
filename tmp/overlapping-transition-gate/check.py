"""Exhaustive finite compatibility test for overlapping invariant embeddings."""
from itertools import combinations, permutations
from collections import Counter
from pathlib import Path
import json

N=4
def partial_bijections():
    for k in range(N+1):
        for domain in combinations(range(N),k):
            for image in permutations(range(N),k):
                yield dict(zip(domain,image))

CASES=[
    ('add_vs_square_all_inputs',tuple(range(N)),lambda x,u:(x+u)%N,lambda y,u:(y*y+u)%N),
    ('increment_vs_xor_one',(0,),lambda x,u:(x+1)%N,lambda y,u:y^1),
    ('identity_vs_square',(0,),lambda x,u:x,lambda y,u:(y*y)%N),
    ('identical_add',tuple(range(N)),lambda x,u:(x+u)%N,lambda y,u:(y+u)%N),
    ('relabeled_add',tuple(range(N)),lambda x,u:(x+u)%N,lambda y,u:(((y^3)+u)%N)^3),
]
relations=list(partial_bijections())
assert len(relations)==209
records=[]
for name,inputs,left,right in CASES:
    accepted=[]
    rejected=[]
    verified=0
    for relation in relations:
        conflict=None
        for x,y in relation.items():
            for u in inputs:
                a,b=left(x,u),right(y,u)
                if relation.get(a)!=b:
                    conflict=dict(pair=[x,y],input=u,successors=[a,b],
                                  mapped_successor=relation.get(a))
                    break
            if conflict: break
        if conflict:
            rejected.append(dict(relation=sorted(relation.items()),conflict=conflict))
            continue
        # Construct the union quotient. Left states 0..3; shared right states use
        # the corresponding left ID; other right states get fresh IDs.
        eleft=list(range(N))
        eright=[None]*N
        for x,y in relation.items(): eright[y]=x
        next_id=N
        for y in range(N):
            if eright[y] is None:
                eright[y]=next_id
                next_id+=1
        transition={}
        for embedding,source in ((eleft,left),(eright,right)):
            for x in range(N):
                for u in inputs:
                    key=(embedding[x],u)
                    successor=embedding[source(x,u)]
                    if key in transition: assert transition[key]==successor
                    transition[key]=successor
        # Verify through each mode's inverse representation, not relation closure.
        for embedding,source in ((eleft,left),(eright,right)):
            inverse={v:k for k,v in enumerate(embedding)}
            for x in range(N):
                for u in inputs:
                    got=inverse[transition[embedding[x],u]]
                    assert got==source(x,u)
                    verified+=1
        accepted.append(dict(relation=sorted(relation.items()),
                             left_embedding=eleft,right_embedding=eright,
                             state_count=next_id,
                             transition=[[s,u,t] for (s,u),t in sorted(transition.items())]))
    hist=Counter(len(a['relation']) for a in accepted)
    records.append(dict(name=name,inputs=inputs,
                        left_table=[[left(x,u) for u in inputs] for x in range(N)],
                        right_table=[[right(x,u) for u in inputs] for x in range(N)],
                        accepted_histogram=dict(sorted(hist.items())),
                        max_overlap=max(hist),verified_transitions=verified,
                        accepted=accepted,rejected=rejected))
result=dict(states_per_mode=N,relations_per_case=len(relations),cases=records,
            status='finite design gate, no novel obfuscation or Wasm claim')
Path(__file__).with_name('results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
for r in records:
    print(r['name'],r['accepted_histogram'],'checks',r['verified_transitions'])
