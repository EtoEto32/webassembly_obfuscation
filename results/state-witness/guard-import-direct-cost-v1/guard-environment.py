"""Equality conditions under common arbitrary writes to exported resources.

An application of universal predicate transformation, not a new general logic.
One environment step assigns all public footprint cells, including no-op values.
"""
import argparse,importlib.util,json
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('environment_protocol',HERE/'guard-protocol.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p);c=p.c;eq=c.g.g

def close(guard,writable):
    if guard is None:return None
    atoms=[]
    def replace(t):return ('u',t[1]) if t[0] in ('l','r') and t[1] in writable else t
    for a,b in guard:
        x,y=replace(a),replace(b)
        if x==y:continue
        if x[0]=='u' or y[0]=='u':return None
        atoms.append((x,y))
    return eq.canonical(atoms)

def prepare(model,left,right,contract='public',protocol='terminal',host_writes=True):
    prepared=p.prepare(model,left,right,contract,protocol)
    prepared['model']=model
    writable=frozenset(i for i in model['cells'] if host_writes and i//c.g.BASE in model['publicResources'])
    prepared['writable']=writable
    prepared['foreignReference']=257+model['functions']
    edges=prepared['edges'];layers=[[frozenset() for _ in edges]]
    for _ in range(1024):
        old=layers[-1]
        new=[eq.combine(close(old[index],writable),*[eq.combine(e['local'],frozenset() if e['terminal'] else c.pullback(old[e['target']],e['left'],e['right'])) for e in row]) for index,row in enumerate(edges)]
        if new==old:break
        layers.append(new)
    else:raise eq.Unsupported('environment fixed-point iteration bound')
    proof=prepared['proof'];final=layers[-1][0]
    guard=eq.canonical([(('m',a[1]) if a[0] in ('l','r') else a,('m',b[1]) if b[0] in ('l','r') else b) for a,b in final]) if final is not None else None
    proof.update(guard=c.serial(guard),status='conditional' if guard else 'impossible' if guard is None else 'unconditional',
        hostWrites='public-footprint' if host_writes else 'none',writableCells=sorted(writable),iterations=len(layers),
        foreignReference=prepared['foreignReference'],lengthMetric='guest call or bulk host assignment, each costs one')
    for state,value in zip(proof['states'],layers[-1]):state['guard']=c.serial(value)
    prepared['layers']=layers
    return prepared

def assignments(prepared,left,right):
    cells=sorted(prepared['writable']);base={i:0 if i<c.g.BASE else 256 for i in cells}
    yield base
    for i in cells:
        other=base.copy();other[i]=1 if i<c.g.BASE else prepared['foreignReference'];yield other

def extract(prepared,values):
    layers,edges=prepared['layers'],prepared['edges'];left,right=values.copy(),values.copy()
    if c.holds(layers[-1][0],left,right):return None
    rank=next(i for i,layer in enumerate(layers) if not c.holds(layer[0],left,right));shortest=rank;state=0;steps=[]
    while rank>0:
        found=False
        for e in edges[state]:
            if not c.holds(e['local'],left,right):
                args=[next((i for i in sorted(left) if i<c.g.BASE and left[i]!=right[i]),0)] if e['observation']=='read-byte' else []
                steps.append({'kind':'call','name':e['action'],'args':args});assert len(steps)==shortest
                return {'steps':steps,'shortestLength':shortest,'guestCalls':sum(x['kind']=='call' for x in steps),'hostWrites':sum(x['kind']=='write' for x in steps)}
            if e['terminal']:continue
            lv,rv=c.apply(e['left'],left),c.apply(e['right'],right)
            if not c.holds(layers[rank-1][e['target']],lv,rv):
                steps.append({'kind':'call','name':e['action'],'args':[0] if e['observation']=='read-byte' else []})
                state=e['target'];left,right=lv,rv;rank-=1;found=True;break
        if found:continue
        for writes in assignments(prepared,left,right):
            lv,rv={**left,**writes},{**right,**writes}
            if not c.holds(layers[rank-1][state],lv,rv):
                steps.append({'kind':'write','cells':[[i,v] for i,v in sorted(writes.items())]})
                left,right=lv,rv;rank-=1;found=True;break
        assert found,'no concrete environment witness'
    raise AssertionError('rank zero')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--left',required=True);a.add_argument('--right',required=True)
    a.add_argument('--contract',choices=['full','public','returns'],default='public');a.add_argument('--protocol',choices=['terminal','reenter'],default='terminal')
    v=a.parse_args()
    if v.out.exists():a.error('output exists')
    if any(x not in '01' for x in v.left+v.right):a.error('segment bits must be 0 or 1')
    result=prepare(c.parse(k.p.read(v.source)),[x=='1' for x in v.left],[x=='1' for x in v.right],v.contract,v.protocol)['proof']
    v.out.write_text(json.dumps(result,indent=2));print(result['status'])
