"""Exhaustive SC micro-model; separate from the native Wasm tests."""
import argparse,collections,json
from pathlib import Path

def explore(early):
    # Two operations: a=x+1, b=3*a, x=7. Two workers, one writer per cell.
    initial=((0,0),(0,0),((-1,0,0),(-1,0,0)))
    queue=collections.deque([initial]);paths={initial:[]};outcomes=set();counterexample=None
    while queue:
        state=queue.popleft();status,values,workers=state
        if all(w[0]<0 for w in workers) and status==(3,3):
            outcomes.add(values[1])
            if values[1]!=24:counterexample=paths[state]
        for wi,(node,stage,v) in enumerate(workers):
            if node<0:
                choices=[i for i in range(2) if status[i]==0 and (i==0 or status[0]==3)]
                actions=[(i,0,8 if i==0 else values[0]*3) for i in choices]
            else:actions=[(node,stage+1,v)]
            for action in actions:
                ss=list(status);vv=list(values);ww=list(workers)
                if node<0:
                    target=action[0];ss[target]=1;ww[wi]=action;desc=f'worker{wi}: claim node{target}, compute {action[2]}'
                else:
                    if (stage==0)==early:ss[node]=3;desc=f'worker{wi}: publish ready node{node}'
                    else:vv[node]=v;desc=f'worker{wi}: store value node{node}={v}'
                    ww[wi]=(-1,0,0) if stage==1 else action
                nxt=(tuple(ss),tuple(vv),tuple(ww))
                if nxt not in paths:paths[nxt]=paths[state]+[desc];queue.append(nxt)
    return dict(states=len(paths),outcomes=sorted(outcomes),counterexample=counterexample)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('output');v=a.parse_args();good=explore(False);bad=explore(True)
    assert good['outcomes']==[24] and 0 in bad['outcomes']
    Path(v.output).write_text(json.dumps(dict(correct=good,early_ready=bad,scope='two-operation two-worker SC model, not full Wasm model checking'),indent=2))
