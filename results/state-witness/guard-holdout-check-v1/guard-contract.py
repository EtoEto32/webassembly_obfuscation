"""Relational equality conditions for chosen API-boundary observations.

Two stores are retained after calls. Equal segment flags do NOT justify early
termination when private store differences may flow to a later observation.
"""
import argparse,importlib.util,json
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('table_guard',HERE/'guard-table.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
def parse(module):
    model=g.parse(module);model['publicResources']=sorted({0 if e[2][0]=='memory' else int(e[2][1])+1 for e in k.p.section(module,'export') if e[2][0] in ('memory','table')})
    funcs=k.p.section(module,'func');byname={json.loads(e[1]):funcs[int(e[2][1])] for e in k.p.section(module,'export') if e[2][0]=='func'}
    for a in model['actions']:
        body=[n for n in byname[a['name']][1:] if n[0] not in k.p.DECL]
        a['observation']='read-byte' if body==[['i32.load8_u',['local.get','0']]] else 'constant' if a['readonly'] else 'void'
    return model
def serial(guard):return None if guard is None else [[list(a),list(b)] for a,b in sorted(guard)]
def side_term(side,term):return (side,term[1]) if term[0]=='m' else term
def post(side,mapping,cell):return side_term(side,mapping.get(cell,g.g.M(cell)))
def pullback(guard,left,right):
    if guard is None:return None
    def sub(t):return post(t[0],left if t[0]=='l' else right,t[1]) if t[0] in ('l','r') else t
    return g.g.canonical([(sub(a),sub(b)) for a,b in guard])
def holds(guard,left,right):
    if guard is None:return False
    def value(t):return t[1] if t[0]=='c' else (right if t[0]=='r' else left)[t[1]]
    return all(value(a)==value(b) for a,b in guard)
def apply(mapping,values):
    result=values.copy()
    for i,t in mapping.items():result[i]=t[1] if t[0]=='c' else values[t[1]]
    return result
def prepare(model,left,right,contract='public'):
    if contract not in ('full','public','returns'):raise ValueError('unknown contract')
    for side in (left,right):
        if len(side)!=len(model['segments']):raise ValueError('segment state length')
        if any(v and not s['initialLive'] for v,s in zip(side,model['segments'])):raise ValueError('cannot revive segment')
    observed=set(model['resources']) if contract=='full' else set(model['publicResources']) if contract=='public' else set()
    visible=[i for i in model['cells'] if i//g.BASE in observed]
    initial=(tuple(left),tuple(right));states=[initial];indices={initial:0};edges=[]
    for a,b in states:
        if len(states)>1024:raise g.g.Unsupported('segment-state-pair bound')
        row=[]
        for action in model['actions']:
            l,r=g.effect(model,a,action),g.effect(model,b,action);target=(l['alive'],r['alive'])
            if target not in indices:indices[target]=len(states);states.append(target)
            atoms=[(post('l',l['mapping'],i),post('r',r['mapping'],i)) for i in visible]
            if action['observation']=='read-byte':atoms += [(('l',i),('r',i)) for i in model['cells'] if i<g.BASE]
            local=g.g.canonical(atoms) if l['outcome']==r['outcome'] else None
            row.append({'action':action['name'],'observation':action['observation'],'target':indices[target],'local':local,
              'left':l['mapping'],'right':r['mapping'],'outcomes':[l['outcome'],r['outcome']]})
        edges.append(row)
    layers=[[frozenset() for _ in states]]
    for _ in range(1024):
        old=layers[-1];new=[g.g.combine(*[g.g.combine(e['local'],pullback(old[e['target']],e['left'],e['right'])) for e in row]) for row in edges]
        if new==old:break
        layers.append(new)
    else:raise g.g.Unsupported('fixed-point iteration bound')
    final=layers[-1][0]
    initialguard=g.g.canonical([(('m',a[1]) if a[0] in ('l','r') else a,('m',b[1]) if b[0] in ('l','r') else b) for a,b in final]) if final is not None else None
    proof={'status':'conditional' if initialguard else 'impossible' if initialguard is None else 'unconditional','guard':serial(initialguard),
      'contract':contract,'observedResources':sorted(observed),'iterations':len(layers),
      'states':[{'left':list(a),'right':list(b),'guard':serial(v)} for (a,b),v in zip(states,layers[-1])],
      'cells':model['cells'],'resources':model['resources'],'functions':model['functions']}
    return {'proof':proof,'layers':layers,'edges':edges}
def extract(prepared,values):
    layers,edges=prepared['layers'],prepared['edges'];left,right=values.copy(),values.copy()
    if holds(layers[-1][0],left,right):return None
    rank=next(i for i,layer in enumerate(layers) if not holds(layer[0],left,right));shortest=rank;state=0;word=[]
    while rank>0:
        found=False
        for e in edges[state]:
            if not holds(e['local'],left,right):
                args=[]
                if e['observation']=='read-byte':
                    i=next((i for i in sorted(left) if i<g.BASE and left[i]!=right[i]),None)
                    # A difference in another visible resource may also be present;
                    # any common valid byte input suffices to observe that resource.
                    args=[i if i is not None else 0]
                word.append({'name':e['action'],'args':args});assert len(word)==shortest
                return {'calls':word,'shortestLength':shortest}
            lv,rv=apply(e['left'],left),apply(e['right'],right)
            if not holds(layers[rank-1][e['target']],lv,rv):
                args=[0] if e['observation']=='read-byte' else []
                word.append({'name':e['action'],'args':args});state=e['target'];left,right=lv,rv;rank-=1;found=True;break
        assert found
    raise AssertionError('rank zero')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--left',required=True);p.add_argument('--right',required=True);p.add_argument('--contract',choices=['full','public','returns'],default='public');v=p.parse_args()
    if any(c not in '01' for c in v.left+v.right):p.error('segment bits must be 0 or 1')
    try:r=prepare(parse(k.p.read(v.source)),[c=='1' for c in v.left],[c=='1' for c in v.right],v.contract)['proof']
    except ValueError as e:r={'status':'unsupported','reason':str(e)}
    v.out.write_text(json.dumps(r,indent=2));print(r['status'])
