import itertools
from pathlib import Path
import sys
import prototype as p


def subspaces(n):
    spaces={frozenset([0]):[]}
    pending=[frozenset([0])]
    while pending:
        old=pending.pop()
        for x in range(1,1<<n):
            if x in old:continue
            new=frozenset(set(old)|{v^x for v in old})
            if new not in spaces:spaces[new]=spaces[old]+[x];pending.append(new)
    return sorted(spaces.values(),key=len)


def main(dest):
    out=Path(dest).resolve();out.mkdir(parents=True,exist_ok=False);n=3;spaces=subspaces(n)
    matrices=[list(rows) for rows in itertools.product(range(1<<n),repeat=n) if p.m.inverse(list(rows)) is not None]
    operations=[(d,s,1) for d in range(n) for s in range(n) if d!=s]
    count=0;states=0;distribution={};witness=None
    for ops in itertools.product(operations,repeat=2):
        for b in matrices:
            info=p.plan(n,ops,b);ps=info['side_prefix'];ds=info['delta'];v=info['side_v']
            best=next(len(candidate) for candidate in spaces if all(all(p.decoder(prefix+candidate)(row) is not None for row in d) for prefix,d in zip(ps,ds)))
            if best!=len(v):raise AssertionError(('greedy not optimal',ops,b,v,best))
            key=str((info['joint_rank'],len(v)));distribution[key]=distribution.get(key,0)+1
            if witness is None and len(v)<info['joint_rank']:witness=dict(ops=ops,b=b,old_rank=info['joint_rank'],new_rank=len(v))
            for prefix,delta,repair in zip(ps,ds,info['side_repairs']):
                for x in itertools.product((0,1),repeat=n):
                    actual=p.m.apply(repair['coeff'],p.m.apply(prefix,x)+p.m.apply(v,x))
                    expected=p.m.apply(delta,x)
                    if actual!=expected:raise AssertionError('repair mismatch')
                    states+=1
            count+=1
    # Non-nested side information permits cyclic coding gains: reject it.
    try:p.saves([[1],[2]],[[2],[1]])
    except ValueError:non_nested_rejected=True
    else:raise AssertionError('accepted non-nested')
    result=dict(instances=count,subspaces=len(spaces),invertible_matrices=len(matrices),state_prefix_checks=states,
                minimum_rank_mismatches=0,distribution=distribution,reduction_witness=witness,non_nested_rejected=non_nested_rejected)
    p.q.save(out/'model.json',result);print(result)


if __name__=='__main__':main(sys.argv[1])
