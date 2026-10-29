"""Construct import inputs from failed equality conditions without an SMT solver."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('direct_imports',HERE/'guard-import.py');i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)

def writable(model):return [c for c in model['cells'] if c//i.g.BASE in model['publicResources']]

def defaults(model):return {c:0 if c<i.g.BASE else 256 for c in writable(model)}

def falsify(model,guard,left,right):
    # A base assignment plus one changed cell is sufficient to falsify any
    # universally invalid equality atom. Sorts have two distinct representatives.
    base=defaults(model)
    if not i.c.holds(guard,{**left,**base},{**right,**base}):return base
    for cell in base:
        assignment=base.copy();assignment[cell]=1 if cell<i.g.BASE else 257+model['functions']
        if not i.c.holds(guard,{**left,**assignment},{**right,**assignment}):return assignment
    raise AssertionError('universal equality failed without a two-value counterexample')

def host_requirements(model,edge,following,contract,protocol):
    left,right=edge['paths'];assert [v['label'] for v in left]==[v['label'] for v in right]
    terminal=protocol=='terminal' and left[-1]['outcome']=='trap'
    guard=i.eq.combine(i.observation(model,contract),frozenset() if terminal else following);requirements={}
    public=i.observation(model,'public');cells=set(writable(model))
    for bi in reversed(range(len(left))):
        l,r=left[bi],right[bi]
        if l['label'][0]=='host':
            requirements[bi]=guard;summary=model['summaries'][l['label'][1:]]
            if summary['writes']=='public':guard=i.e.close(guard,cells)
            elif summary['writes']=='may-public':guard=i.eq.combine(guard,i.e.close(guard,cells))
            if summary['reads']=='public':guard=i.eq.combine(public,guard)
        guard=i.c.pullback(guard,l['mapping'],r['mapping'])
    return requirements

def simulate(model,edge,left,right,writes,contract):
    stores=[];traces=[];public=writable(model)
    for path,values in zip(edge['paths'],(left,right)):
        values=values.copy();trace=[]
        for bi,event in enumerate(path):
            values=i.c.apply(event['mapping'],values);label=event['label']
            if label[0]=='host':
                summary=model['summaries'][label[1:]];read=tuple(values[c] for c in public) if summary['reads']=='public' else None
                trace.append((label,read));assignment=writes.get(bi,{})
                if summary['writes']=='public':assert set(assignment)==set(public),'missing mandatory write'
                elif summary['writes']=='none':assert not assignment
                else:assert set(assignment)<=set(public)
                values.update(assignment)
            else:trace.append((label,None))
        stores.append(values);traces.append(trace)
    visible=model['cells'] if contract=='full' else public if contract=='public' else []
    different=traces[0]!=traces[1] or any(stores[0][c]!=stores[1][c] for c in visible)
    return stores[0],stores[1],different

def choose(model,edge,following,contract,protocol,left,right):
    paths=edge['paths'];labels=[[v['label'] for v in p] for p in paths];base=defaults(model);writes={}
    # Fill even imports after the first distinguishing observation, so the
    # resulting entire API call is executable under its mandatory-write contract.
    for path in paths:
        for bi,event in enumerate(path):
            if event['label'][0]=='host' and model['summaries'][event['label'][1:]]['writes']=='public':writes[bi]=base.copy()
    if labels[0]==labels[1]:
        requirements=host_requirements(model,edge,following,contract,protocol);lv,rv=left.copy(),right.copy();already_different=False
        public=i.observation(model,'public')
        for bi,(l,r) in enumerate(zip(*paths)):
            lv,rv=i.c.apply(l['mapping'],lv),i.c.apply(r['mapping'],rv)
            if l['label'][0]!='host':continue
            summary=model['summaries'][l['label'][1:]]
            if summary['reads']=='public' and not i.c.holds(public,lv,rv):already_different=True
            if not already_different:
                need=requirements[bi]
                if summary['writes']=='public':writes[bi]=falsify(model,need,lv,rv)
                elif summary['writes']=='may-public':
                    writes[bi]={} if not i.c.holds(need,lv,rv) else falsify(model,need,lv,rv)
            lv.update(writes.get(bi,{}));rv.update(writes.get(bi,{}))
    lv,rv,different=simulate(model,edge,left,right,writes,contract)
    if not different:assert not i.c.holds(following,lv,rv),'counterexample construction lost the failure'
    return lv,rv,different,[{'block':bi,'cells':sorted(values.items())} for bi,values in sorted(writes.items())]

def witness(prepared,values):
    model=prepared['model'];proof=prepared['proof'];layers=prepared['layers'];left=right=values.copy()
    if set(values)!=set(model['cells']):raise ValueError('store must specify exactly the footprint cells')
    if any(not isinstance(v,int) or isinstance(v,bool) or (not 0<=v<=255 if c<i.g.BASE else v<256) for c,v in values.items()):raise ValueError('invalid store value')
    if i.c.holds(layers[-1][0],left,right):return None
    state=0;rank=next(n for n,layer in enumerate(layers) if not i.c.holds(layer[0],left,right));calls=[]
    while rank:
        for edge in prepared['edges'][state]:
            following=layers[rank-1][edge['target']]
            wp=i.transform(model,edge,following,proof['contract'],proof['protocol'])
            if i.c.holds(wp,left,right):continue
            left,right,different,writes=choose(model,edge,following,proof['contract'],proof['protocol'],left,right)
            calls.append({'name':edge['action'],'writes':writes})
            if different:return {'calls':calls,'apiLength':len(calls),'minimality':'not claimed','solver':'none','masks':'no-op or full footprint overwrite'}
            state=edge['target'];rank-=1;break
        else:raise AssertionError('failed layer without an action')
    raise AssertionError('rank zero without observation')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('summaries',type=Path);a.add_argument('store',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--left',required=True);a.add_argument('--right',required=True);a.add_argument('--observation',choices=['full','public','returns'],required=True);a.add_argument('--after-trap',choices=['terminal','reenter'],required=True);v=a.parse_args()
    if v.out.exists():a.error('output exists')
    if any(c not in '01' for c in v.left+v.right):a.error('bits must be 0 or 1')
    summaries={(r['module'],r['field']):{k:r[k] for k in ('reads','writes')} for r in json.loads(v.summaries.read_text())}
    model=i.parse(i.k.p.read(v.source),summaries);p=i.prepare(model,[x=='1' for x in v.left],[x=='1' for x in v.right],v.observation,v.after_trap)
    result={'proof':p['proof'],'witness':witness(p,dict(json.loads(v.store.read_text())['cells'])),'sourceSha256':hashlib.sha256(v.source.read_bytes()).hexdigest()}
    v.out.write_text(json.dumps(result,indent=2));print('different' if result['witness'] else 'condition-satisfied')
