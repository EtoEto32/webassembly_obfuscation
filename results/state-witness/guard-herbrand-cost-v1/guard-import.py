"""Finite equality conditions with explicit synchronous void host summaries.

Uses ordinary relational weakest preconditions, with a universal host input at
each matching import. It neither verifies the summary nor analyses resume PCs.
"""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('import_environment',HERE/'guard-environment.py')
e=importlib.util.module_from_spec(s);s.loader.exec_module(e);c=e.c;g=c.g;eq=g.g


def flatten(nodes):
    result=[]
    for n in nodes:
        if n[0]=='loop':
            if any(not isinstance(x,list) or x[0] in k.p.DECL for x in n[1:]):
                raise eq.Unsupported('only untyped one-pass loops')
            result.extend(flatten(n[1:]))
        elif n[0]=='br_if' and len(n)==3 and n[2]==['i32.const','0']:
            result.append(['nop'])
        elif n[0]=='i32.store8' and len(n)==3:
            # Constant store8 and a length-one fill have the same byte/trap effect.
            result.append(['memory.fill',n[1],n[2],['i32.const','1']])
        else:result.append(n)
    return result


def parse(module,summaries,offsets=None):
    offsets=offsets or {};imports=k.p.section(module,'import');types=k.p.section(module,'type')
    stubs=[];names=[]
    for imp in imports:
        if imp[3][0]!='func':raise eq.Unsupported('only function imports')
        decl=imp[3];typeid=int(next(n[1] for n in decl[1:] if n[0]=='type'))
        if types[typeid][1]!=['func']:raise eq.Unsupported('imports must be void with no arguments')
        name=(json.loads(imp[1]),json.loads(imp[2]))
        if name not in summaries:raise eq.Unsupported('missing host summary: '+repr(name))
        summary=summaries[name]
        if summary.get('reads') not in ('none','public') or summary.get('writes') not in ('none','public','may-public'):
            raise eq.Unsupported('host summary: reads none/public; writes none/public (mandatory overwrite)/may-public')
        names.append(name);stubs.append(['func',['type',str(typeid)],['nop']])
    funcs=k.p.section(module,'func');original_count=len(imports)+len(funcs)
    # Preserve original function indices, including element references. Synthetic
    # chunk functions are an internal parsing aid and never occur in descriptors.
    base=['module']+[copy.deepcopy(n) for n in module[1:] if n[0] not in ('import','func','export')]
    base.extend(stubs)
    for f in funcs:base.append(['func']+[copy.deepcopy(n) for n in f[1:] if n[0] in k.p.DECL]+[['nop']])
    base.extend(copy.deepcopy(n) for n in k.p.section(module,'export') if n[2][0]!='func')
    exports=[n for n in k.p.section(module,'export') if n[2][0]=='func'];plans=[]
    if set(offsets)-{json.loads(n[1]) for n in exports}:raise eq.Unsupported('unknown continuation export')
    chunks=0
    for ex in exports:
        index=int(ex[2][1]);name=json.loads(ex[1])
        if index<len(imports):raise eq.Unsupported('directly exported import excluded')
        f=funcs[index-len(imports)];typeid=int(next(n[1] for n in f[1:] if n[0]=='type'))
        if types[typeid][1]!=['func']:raise eq.Unsupported('exports must be void with no arguments')
        body=flatten([n for n in f[1:] if n[0] not in k.p.DECL]);offset=offsets.get(name,0)
        if not isinstance(offset,int) or offset<0 or offset>len(body):raise eq.Unsupported('invalid continuation offset')
        blocks=[];current=[]
        def flush(host):
            nonlocal chunks,current
            chunk='__chunk_'+str(chunks);idx=original_count+chunks;chunks+=1
            base.append(['func',['type',str(typeid)]]+copy.deepcopy(current or [['nop']]))
            base.append(['export',json.dumps(chunk),['func',str(idx)]])
            blocks.append({'chunk':chunk,'host':host});current=[]
        for n in body[offset:]:
            if n[0]=='call':
                if len(n)!=2 or int(n[1])>=len(imports):raise eq.Unsupported('only direct calls to void imports')
                flush(names[int(n[1])])
            else:current.append(n)
        flush(None);plans.append({'name':name,'blocks':blocks,'offset':offset})
    model=c.parse(base);byname={a['name']:a for a in model['actions']}
    model['functions']=original_count;model['actions']=plans;model['summaries']=summaries
    for action in plans:
        for block in action['blocks']:block['ops']=byname[block.pop('chunk')]['ops']
    model['continuationOffsets']=offsets
    return model


def path(model,alive,action):
    events=[]
    for block in action['blocks']:
        eff=g.effect(model,alive,{'ops':block['ops']});alive=eff['alive']
        label=('end',eff['outcome']) if eff['outcome']=='trap' or block['host'] is None else ('host',*block['host'])
        events.append({**eff,'label':label})
        if label[0]=='end':break
    return events


def observation(model,contract):
    resources=set(model['resources']) if contract=='full' else set(model['publicResources']) if contract=='public' else set()
    return frozenset((('l',i),('r',i)) for i in model['cells'] if i//g.BASE in resources)


def transform(model,edge,following,contract,protocol):
    left,right=edge['paths'];labels=[v['label'] for v in left],[v['label'] for v in right]
    if labels[0]!=labels[1]:return None
    terminal=protocol=='terminal' and left[-1]['outcome']=='trap'
    guard=eq.combine(observation(model,contract),frozenset() if terminal else following)
    public=observation(model,'public');writable={i for i in model['cells'] if i//g.BASE in model['publicResources']}
    for l,r in reversed(list(zip(left,right))):
        if l['label'][0]=='host':
            summary=model['summaries'][l['label'][1:]]
            if summary['writes']=='public':guard=e.close(guard,writable)
            elif summary['writes']=='may-public':guard=eq.combine(guard,e.close(guard,writable))
            if summary['reads']=='public':guard=eq.combine(public,guard)
        guard=c.pullback(guard,l['mapping'],r['mapping'])
    return guard


def prepare(model,left,right,contract='public',protocol='terminal'):
    if contract not in ('full','public','returns') or protocol not in ('terminal','reenter'):raise ValueError('invalid contract')
    for side in (left,right):
        if len(side)!=len(model['segments']):raise ValueError('segment state length')
        if any(x and not s['initialLive'] for x,s in zip(side,model['segments'])):raise ValueError('invalid live segment')
    states=[(tuple(left),tuple(right))];index={states[0]:0};edges=[]
    for pair in states:
        if len(states)>1024:raise eq.Unsupported('state-pair bound')
        row=[]
        for action in model['actions']:
            paths=[path(model,pair[i],action) for i in (0,1)];target=tuple(p[-1]['alive'] for p in paths)
            if target not in index:index[target]=len(states);states.append(target)
            row.append({'action':action['name'],'paths':paths,'target':index[target]})
        edges.append(row)
    layers=[[frozenset() for _ in states]]
    for _ in range(1024):
        old=layers[-1];new=[eq.combine(*[transform(model,edge,old[edge['target']],contract,protocol) for edge in row]) for row in edges]
        if new==old:break
        layers.append(new)
    else:raise eq.Unsupported('fixed-point bound')
    final=layers[-1][0]
    guard=eq.canonical([(('m',a[1]) if a[0] in ('l','r') else a,('m',b[1]) if b[0] in ('l','r') else b) for a,b in final]) if final is not None else None
    proof={'status':'impossible' if guard is None else 'conditional' if guard else 'unconditional','guard':c.serial(guard),
        'contract':contract,'protocol':protocol,'hostSummaries':[{'module':a,'field':b,**v} for (a,b),v in sorted(model['summaries'].items())],
        'continuationOffsets':model['continuationOffsets'],'iterations':len(layers),'cells':model['cells'],'functions':model['functions'],
        'states':[{'left':list(l),'right':list(r),'guard':c.serial(v)} for (l,r),v in zip(states,layers[-1])],
        'premise':'Synchronous void imports, no reentry, grow, host trap, or other side effects. Same host input at matching calls. Supplied summaries are trusted.'}
    return {'model':model,'proof':proof,'layers':layers,'edges':edges}


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('summaries',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--left',required=True);a.add_argument('--right',required=True);a.add_argument('--observation',choices=['full','public','returns'],required=True)
    a.add_argument('--after-trap',choices=['terminal','reenter'],required=True);a.add_argument('--offsets',type=Path)
    v=a.parse_args()
    if v.out.exists():a.error('output exists')
    if any(x not in '01' for x in v.left+v.right):a.error('bits must be 0 or 1')
    summaries={(r['module'],r['field']):{key:r[key] for key in ('reads','writes')} for r in json.loads(v.summaries.read_text())}
    try:
        model=parse(k.p.read(v.source),summaries,json.loads(v.offsets.read_text()) if v.offsets else {})
        proof=prepare(model,[x=='1' for x in v.left],[x=='1' for x in v.right],v.observation,v.after_trap)['proof']
    except (ValueError,KeyError,StopIteration) as err:proof={'status':'unsupported','reason':str(err)}
    proof['sourceSha256']=hashlib.sha256(v.source.read_bytes()).hexdigest();v.out.write_text(json.dumps(proof,indent=2));print(proof['status'])
