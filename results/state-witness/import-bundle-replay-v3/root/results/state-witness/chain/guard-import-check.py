"""Independent array execution at internal import boundaries; shared AST parser."""
import argparse,hashlib,importlib.util,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
i=load('import_guard','guard-import.py');a=load('import_arrays','guard-environment-check.py');z=a.z


def execute(model,alive,action,array,prefix):
    events=[];inputs=[];domain=[];masks=[]
    for bi,block in enumerate(action['blocks']):
        alive,trapped,array=a.a.a.execute(model,alive,{'ops':block['ops']},array)
        if trapped or block['host'] is None:
            events.append({'label':('end','trap' if trapped else 'return'),'array':array});break
        name=block['host'];summary=model['summaries'][name]
        events.append({'label':('host',*name),'array':array})
        if summary['writes'] in ('public','may-public'):
            for cell in model['cells']:
                if cell//i.g.BASE not in model['publicResources']:continue
                value=z.Int(prefix+'_'+str(bi)+'_'+str(cell));inputs.append((bi,cell,value))
                domain.append(z.And(value>=0,value<=255) if cell<i.g.BASE else value>=256)
                if summary['writes']=='may-public':
                    mask=z.Bool(prefix+'_mask_'+str(bi)+'_'+str(cell));masks.append((bi,cell,mask))
                    value=z.If(mask,value,z.Select(array,cell))
                array=z.Store(array,cell,value)
    return {'events':events,'alive':alive,'array':array,'inputs':inputs,'masks':masks,'domain':domain}


def obligation(model,pair,action,left,right,previous,lookup,contract,protocol,prefix='input'):
    l,r=[execute(model,flags,action,array,prefix) for flags,array in zip(pair,(left,right))]
    variables={str(x):x for _,_,x in l['inputs']+r['inputs']+l['masks']+r['masks']};domain=l['domain']+r['domain'];atoms=[]
    labels=[[ev['label'] for ev in run['events']] for run in (l,r)]
    if labels[0]!=labels[1]:atoms.append(z.BoolVal(False))
    else:
        for le,re in zip(l['events'],r['events']):
            if le['label'][0]=='host' and model['summaries'][le['label'][1:]]['reads']=='public':
                atoms += [z.Select(le['array'],cell)==z.Select(re['array'],cell) for cell in model['cells'] if cell//i.g.BASE in model['publicResources']]
    visible=set(model['resources']) if contract=='full' else set(model['publicResources']) if contract=='public' else set()
    atoms += [z.Select(l['array'],cell)==z.Select(r['array'],cell) for cell in model['cells'] if cell//i.g.BASE in visible]
    terminal=protocol=='terminal' and labels[0][-1]==labels[1][-1]==('end','trap')
    if not terminal:atoms.append(a.a.predicate(previous[lookup[(l['alive'],r['alive'])]],l['array'],r['array']))
    body=z.And(*atoms);constraints=z.And(*domain)
    quantified=z.ForAll(list(variables.values()),z.Implies(constraints,body)) if variables else body
    return {'formula':quantified,'body':body,'domain':constraints,'left':l,'right':r}


def check(model,prepared):
    states=prepared['proof']['states'];pairs=[(tuple(s['left']),tuple(s['right'])) for s in states];lookup={p:n for n,p in enumerate(pairs)}
    left,right,domain=a.arrays(model);layers=prepared['layers'];proof=prepared['proof'];checks=[]
    for li in range(1,len(layers)+1):
        previous=layers[li-1];following=layers[min(li,len(layers)-1)]
        for si,pair in enumerate(pairs):
            formulas=[obligation(model,pair,action,left,right,previous,lookup,proof['contract'],proof['protocol'])['formula'] for action in model['actions']]
            solver=z.Solver();solver.set(timeout=5000);solver.add(domain,a.a.predicate(following[si],left,right)!=z.And(*formulas));answer=solver.check()
            assert answer!=z.sat,('recurrence',li,si,str(solver.model()))
            checks.append({'layer':li,'state':si,'answer':str(answer),'reason':solver.reason_unknown() if answer==z.unknown else None})
    common=z.Array('common',z.IntSort(),z.IntSort());_,_,typed=a.arrays(model)
    dom=[z.And(z.Select(common,c)>=0,z.Select(common,c)<=255) if c<i.g.BASE else z.Select(common,c)>=256 for c in model['cells']]
    solver=z.Solver();solver.set(timeout=5000);solver.add(*dom,a.a.predicate(layers[-1][0],common,common)!=a.a.predicate(proof['guard'],common,common));answer=solver.check()
    assert answer!=z.sat,'initial projection';checks.append({'projection':True,'answer':str(answer)})
    return checks


def witness(prepared,values):
    model=prepared['model'];layers=prepared['layers'];proof=prepared['proof'];left=right=values.copy()
    if i.c.holds(layers[-1][0],left,right):return None
    pairs=[(tuple(s['left']),tuple(s['right'])) for s in proof['states']];lookup={p:n for n,p in enumerate(pairs)}
    state=0;rank=next(n for n,v in enumerate(layers) if not i.c.holds(v[0],left,right));calls=[]
    while rank:
        la=ra=z.K(z.IntSort(),z.IntVal(0))
        for cell,value in left.items():la=z.Store(la,cell,value)
        for cell,value in right.items():ra=z.Store(ra,cell,value)
        for action,edge in zip(model['actions'],prepared['edges'][state]):
            wp=i.transform(model,edge,layers[rank-1][edge['target']],proof['contract'],proof['protocol'])
            if i.c.holds(wp,left,right):continue
            result=obligation(model,pairs[state],action,la,ra,layers[rank-1],lookup,proof['contract'],proof['protocol'])
            solver=z.Solver();solver.set(timeout=5000);solver.add(result['domain'],z.Not(result['body']));answer=solver.check()
            if answer!=z.sat:raise ValueError('counterexample solver '+str(answer))
            solution=solver.model();writes={}
            masks={(bi,cell):var for bi,cell,var in result['left']['masks']+result['right']['masks']}
            for bi,cell,var in result['left']['inputs']+result['right']['inputs']:
                if (bi,cell) in masks and not z.is_true(solution.eval(masks[(bi,cell)],model_completion=True)):continue
                writes.setdefault(bi,{})[cell]=solution.eval(var,model_completion=True).as_long()
            calls.append({'name':action['name'],'writes':[{'block':bi,'cells':sorted(cells.items())} for bi,cells in sorted(writes.items())]})
            nofuture=obligation(model,pairs[state],action,la,ra,[frozenset() for _ in pairs],lookup,proof['contract'],proof['protocol'])
            if not z.is_true(solution.eval(nofuture['body'],model_completion=True)):
                return {'calls':calls,'apiLength':len(calls),'minimality':'not claimed; SMT-selected import inputs'}
            left={cell:solution.eval(z.Select(result['left']['array'],cell),model_completion=True).as_long() for cell in model['cells']}
            right={cell:solution.eval(z.Select(result['right']['array'],cell),model_completion=True).as_long() for cell in model['cells']}
            state=lookup[(result['left']['alive'],result['right']['alive'])];rank-=1;break
        else:raise AssertionError('failed rank without witness')
    raise AssertionError('rank zero')


if __name__=='__main__':
    arg=argparse.ArgumentParser();arg.add_argument('source',type=Path);arg.add_argument('out',type=Path);v=arg.parse_args();v.out.mkdir(parents=True,exist_ok=False);rows=[]
    for row in json.loads((v.source/'manifest.json').read_text())['rows']:
        summaries={(q['module'],q['field']):{k:q[k] for k in ('reads','writes')} for q in row['proof']['hostSummaries']}
        model=i.parse(i.k.p.read(v.source/row['source']),summaries,row['proof']['continuationOffsets'])
        prepared=i.prepare(model,row['left'],row['right'],row['proof']['contract'],row['proof']['protocol']);assert json.loads(json.dumps(prepared['proof']))==row['proof']
        rows.append({'name':row['name'],'checks':check(model,prepared)})
    result={'rows':rows,'contracts':len(rows),'unsat':sum(q['answer']=='unsat' for r in rows for q in r['checks']),'unknown':sum(q['answer']=='unknown' for r in rows for q in r['checks']),'z3':z.get_version_string()}
    (v.out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,v.out/name)
    (v.out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in v.out.iterdir()},indent=2));print(json.dumps({k:x for k,x in result.items() if k!='rows'}))
