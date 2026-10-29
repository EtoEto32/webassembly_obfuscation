"""Trap-terminal or re-entrant protocols over the frozen two-store model."""
import argparse,importlib.util,json
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('contract',HERE/'guard-contract.py');c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)

def terminal(model,action,left_outcome,right_outcome):
    return left_outcome==right_outcome=='trap' or action['observation']=='read-byte' and model['resources'][0]['length']==0

def prepare(model,left,right,contract='public',protocol='terminal'):
    if protocol not in ('terminal','reenter'):raise ValueError('unknown protocol')
    prepared=c.prepare(model,left,right,contract);actions={a['name']:a for a in model['actions']};edges=prepared['edges']
    for row in edges:
        for e in row:e['terminal']=protocol=='terminal' and terminal(model,actions[e['action']],*e['outcomes'])
    layers=[[frozenset() for _ in edges]]
    for _ in range(1024):
        old=layers[-1];new=[c.g.g.combine(*[c.g.g.combine(e['local'],frozenset() if e['terminal'] else c.pullback(old[e['target']],e['left'],e['right'])) for e in row]) for row in edges]
        if new==old:break
        layers.append(new)
    else:raise c.g.g.Unsupported('protocol fixed-point iteration bound')
    proof=prepared['proof'];final=layers[-1][0]
    guard=c.g.g.canonical([(('m',a[1]) if a[0] in ('l','r') else a,('m',b[1]) if b[0] in ('l','r') else b) for a,b in final]) if final is not None else None
    proof.update(protocol=protocol,guard=c.serial(guard),status='conditional' if guard else 'impossible' if guard is None else 'unconditional',iterations=len(layers))
    for s,v in zip(proof['states'],layers[-1]):s['guard']=c.serial(v)
    prepared['layers']=layers;return prepared

def extract(prepared,values):
    layers,edges=prepared['layers'],prepared['edges'];left,right=values.copy(),values.copy()
    if c.holds(layers[-1][0],left,right):return None
    rank=next(i for i,layer in enumerate(layers) if not c.holds(layer[0],left,right));shortest=rank;state=0;word=[]
    while rank>0:
        found=False
        for e in edges[state]:
            if not c.holds(e['local'],left,right):
                args=[]
                if e['observation']=='read-byte':args=[next((i for i in sorted(left) if i<c.g.BASE and left[i]!=right[i]),0)]
                word.append({'name':e['action'],'args':args});assert len(word)==shortest
                return {'calls':word,'shortestLength':shortest}
            if e['terminal']:continue
            lv,rv=c.apply(e['left'],left),c.apply(e['right'],right)
            if not c.holds(layers[rank-1][e['target']],lv,rv):
                word.append({'name':e['action'],'args':[0] if e['observation']=='read-byte' else []});state=e['target'];left,right=lv,rv;rank-=1;found=True;break
        assert found
    raise AssertionError('rank zero')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--left',required=True);p.add_argument('--right',required=True)
    p.add_argument('--contract',choices=['full','public','returns'],default='public');p.add_argument('--protocol',choices=['terminal','reenter'],default='terminal');v=p.parse_args()
    if any(x not in '01' for x in v.left+v.right):p.error('segment bits must be 0 or 1')
    try:r=prepare(c.parse(k.p.read(v.source)),[x=='1' for x in v.left],[x=='1' for x in v.right],v.contract,v.protocol)['proof']
    except ValueError as e:r={'status':'unsupported','reason':str(e)}
    v.out.write_text(json.dumps(r,indent=2));print(r['status'])
