"""Recover a shortest distinguishing API word from equality fixed-point layers.

Known model-checking counterexample reconstruction, specialized to the bulk API
profile. Concrete BFS is included as a fair finite-state baseline.
"""
import argparse,collections,importlib.util,json,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('table_guard',HERE/'guard-table.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)

def satisfied(guard,values):
    if guard is None:return False
    value=lambda t:t[1] if t[0]=='c' else values[t[1]]
    return all(value(x)==value(y) for x,y in guard)

def apply(mapping,values):
    result=values.copy()
    for c,t in mapping.items():result[c]=t[1] if t[0]=='c' else values[t[1]]
    return result

def validate_values(model,values):
    for c in model['cells']:
        v=values[c];r=model['resources'][c//g.BASE]
        if not isinstance(v,int):raise ValueError('noninteger cell')
        if not ((0<=v<=255) if r['kind']=='memory' else (256<=v<=256+model['functions'])):raise ValueError('ill-typed cell value')

def prepare(model,left,right):
    proof=g.solve(model,left,right);states=proof['states']
    index={(tuple(s['left']),tuple(s['right'])):i for i,s in enumerate(states)};edges=[]
    for s in states:
        row=[]
        if s['left']!=s['right']:
            for action in model['actions']:
                if action['readonly']:continue
                a,b=g.effect(model,s['left'],action),g.effect(model,s['right'],action)
                cells=set(a['mapping'])|set(b['mapping'])
                local=g.g.canonical([(a['mapping'].get(i,g.g.M(i)),b['mapping'].get(i,g.g.M(i))) for i in cells]) if a['outcome']==b['outcome'] else None
                row.append({'action':action['name'],'target':index[(a['alive'],b['alive'])],'local':local,'mapping':a['mapping']})
        edges.append(row)
    layers=[[frozenset() for _ in states]]
    for _ in range(1024):
        old=layers[-1]
        new=[g.g.combine(*[g.g.combine(e['local'],g.g.pullback(old[e['target']],e['mapping'])) for e in row]) for row in edges]
        if new==old:break
        layers.append(new)
    else:raise g.g.Unsupported('layer bound')
    serial=lambda v:None if v is None else [[list(a),list(b)] for a,b in sorted(v)]
    assert [serial(v) for v in layers[-1]]==[s['guard'] for s in states]
    assert len(layers)==proof['iterations']
    return {'proof':proof,'layers':layers,'edges':edges}

def extract(prepared,values):
    layers,edges=prepared['layers'],prepared['edges']
    if satisfied(layers[-1][0],values):return None
    rank=next(i for i,layer in enumerate(layers) if not satisfied(layer[0],values));shortest=rank
    state=0;word=[]
    while rank>0:
        found=False
        for e in edges[state]:
            if not satisfied(e['local'],values):
                word.append(e['action']);assert len(word)==shortest
                return {'word':word,'shortestLength':shortest,'failureRank':rank}
            after=apply(e['mapping'],values)
            if not satisfied(layers[rank-1][e['target']],after):
                word.append(e['action']);values=after;state=e['target'];rank-=1;found=True;break
        assert found,'failed guard has no causal edge'
    raise AssertionError('rank zero must be true')

def concrete_bfs(model,left,right,values,budget=100000):
    cells=model['cells'];initial=(tuple(left),tuple(right),tuple(values[c] for c in cells))
    queue=collections.deque([(initial,[])]);seen={initial};transitions=0
    while queue:
        (left,right,data),prefix=queue.popleft()
        if left==right:continue
        before=dict(zip(cells,data))
        for action in model['actions']:
            if action['readonly']:continue
            a,b=g.effect(model,left,action),g.effect(model,right,action);transitions+=1
            av,bv=apply(a['mapping'],before),apply(b['mapping'],before)
            word=prefix+[action['name']]
            if a['outcome']!=b['outcome'] or av!=bv:return {'status':'witness','word':word,'states':len(seen),'transitions':transitions}
            target=(a['alive'],b['alive'],tuple(av[c] for c in cells))
            if target not in seen:
                if len(seen)>=budget:return {'status':'budget','states':len(seen),'transitions':transitions}
                seen.add(target);queue.append((target,word))
    return {'status':'equivalent','word':None,'states':len(seen),'transitions':transitions}

def main(source,left,right,store,out):
    model=g.parse(k.p.read(source));values={int(c):v for c,v in json.loads(store.read_text()).items()};validate_values(model,values)
    start=time.perf_counter();prepared=prepare(model,left,right);built=time.perf_counter()-start
    start=time.perf_counter();witness=extract(prepared,values);elapsed=time.perf_counter()-start
    out.write_text(json.dumps({'proof':prepared['proof'],'witness':witness,'prepareSeconds':built,'extractSeconds':elapsed},indent=2))
    print(json.dumps({'status':prepared['proof']['status'],'witnessLength':None if witness is None else len(witness['word'])}))
def bits(s):
    if any(x not in '01' for x in s):raise argparse.ArgumentTypeError('only 0 and 1 are accepted')
    return [x=='1' for x in s]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('store',type=Path);p.add_argument('out',type=Path);p.add_argument('--left',type=bits,required=True);p.add_argument('--right',type=bits,required=True);v=p.parse_args();main(v.source,v.left,v.right,v.store,v.out)
