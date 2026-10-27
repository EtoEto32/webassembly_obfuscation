"""Generic SMT predicate transformers, QE, and semantic fixed-point checks.

No equality lattice or symbolic copy maps are used in this solver. The parser
and separately encoded array interpreter are shared with the other baselines.
"""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
q=load('generic_array_ops','guard-import-check.py');z=q.z


class Incomplete(Exception):pass


def predicate_environment(model):
    left=right=z.K(z.IntSort(),z.IntVal(0));variables={};domain=[]
    for cell in model['cells']:
        for side in ('left','right'):
            v=z.Int(side+'_'+str(cell));variables[(side,cell)]=v
            if side=='left':left=z.Store(left,cell,v)
            else:right=z.Store(right,cell,v)
            domain.append(z.And(v>=0,v<=255) if cell<q.i.g.BASE else v>=256)
    return left,right,variables,z.And(*domain)


def substitute(formula,variables,left,right):
    replacements=[(v,z.Select(left if side=='left' else right,cell)) for (side,cell),v in variables.items()]
    return z.simplify(z.substitute(formula,*replacements)) if replacements else formula


def transition(model,pair,action,left,right,variables):
    # Independent Store/Select execution, with one common symbol per import cell.
    a,b=[q.execute(model,flags,action,array,'host_input') for flags,array in zip(pair,(left,right))]
    labels=[[event['label'] for event in run['events']] for run in (a,b)];local=[z.BoolVal(labels[0]==labels[1])]
    if labels[0]==labels[1]:
        for le,re in zip(a['events'],b['events']):
            if le['label'][0]=='host' and model['summaries'][le['label'][1:]]['reads']=='public':
                local.extend(z.Select(le['array'],cell)==z.Select(re['array'],cell) for cell in model['cells'] if cell//q.i.g.BASE in model['publicResources'])
    inputs={str(v):v for _,_,v in a['inputs']+b['inputs']+a['masks']+b['masks']}
    return {'left':a,'right':b,'target':(a['alive'],b['alive']),'local':local,'inputs':list(inputs.values()),'inputDomain':z.And(*a['domain'],*b['domain']),
        'bothTrap':labels[0][-1]==labels[1][-1]==('end','trap')}


def solve(model,left_flags,right_flags,contract,protocol,timeout=5000,iterations=1024):
    started=time.perf_counter();left,right,variables,domain=predicate_environment(model)
    states=[(tuple(left_flags),tuple(right_flags))];lookup={states[0]:0};edges=[]
    observed=set(model['resources']) if contract=='full' else set(model['publicResources']) if contract=='public' else set()
    for pair in states:
        if len(states)>1024:raise Incomplete('state-limit')
        row=[]
        for action in model['actions']:
            edge=transition(model,pair,action,left,right,variables)
            if edge['target'] not in lookup:lookup[edge['target']]=len(states);states.append(edge['target'])
            edge['local'].extend(z.Select(edge['left']['array'],cell)==z.Select(edge['right']['array'],cell) for cell in model['cells'] if cell//q.i.g.BASE in observed)
            edge['local']=z.And(*edge['local']);row.append(edge)
        edges.append(row)
    prepared=time.perf_counter()-started;guards=[z.BoolVal(True) for _ in states];qe_calls=equivalence_queries=0;trace=[]
    for iteration in range(1,iterations+1):
        new=[]
        for row in edges:
            formulas=[]
            for edge in row:
                successor=z.BoolVal(True) if protocol=='terminal' and edge['bothTrap'] else substitute(guards[lookup[edge['target']]],variables,edge['left']['array'],edge['right']['array'])
                formula=z.simplify(z.And(edge['local'],successor))
                if edge['inputs']:
                    quantified=z.simplify(z.ForAll(edge['inputs'],z.Implies(edge['inputDomain'],formula)))
                    try:formula=z.TryFor(z.Tactic('qe'),timeout)(quantified).as_expr()
                    except z.Z3Exception as err:raise Incomplete('qe-failure: '+str(err))
                    qe_calls+=1
                formulas.append(formula)
            new.append(z.simplify(z.And(*formulas)))
        equal=True
        for a,b in zip(guards,new):
            solver=z.Solver();solver.set(timeout=timeout);solver.add(domain,a!=b);answer=solver.check();equivalence_queries+=1
            if answer==z.unknown:raise Incomplete('equivalence-unknown: '+solver.reason_unknown())
            if answer==z.sat:equal=False
        guards=new;trace.append({'iteration':iteration,'totalSmtCharacters':sum(len(f.sexpr()) for f in guards),'fixed':equal})
        if equal:break
    else:raise Incomplete('iteration-limit')
    common=substitute(guards[0],variables,left,left)
    return {'formula':common,'variables':variables,'left':left,'right':right,'domain':domain,'guards':guards,
        'summary':{'iterations':iteration,'states':len(states),'qeCalls':qe_calls,'equivalenceQueries':equivalence_queries,'preparationSeconds':prepared,
                   'seconds':time.perf_counter()-started,'trace':trace,'smt':common.sexpr()}}


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];manifest=json.loads((source/'manifest.json').read_text())
    for ri,row in enumerate(manifest['rows']):
        summaries={(s['module'],s['field']):{k:s[k] for k in ('reads','writes')} for s in row['proof']['hostSummaries']}
        model=q.i.parse(q.i.k.p.read(source/row['source']),summaries,row['proof']['continuationOffsets']);proof=row['proof']
        try:
            result=solve(model,row['left'],row['right'],proof['contract'],proof['protocol'])
            expected=q.a.a.predicate(proof['guard'],result['left'],result['left']);solver=z.Solver();solver.set(timeout=5000)
            solver.add(result['domain'],expected!=result['formula']);answer=solver.check()
            status='same-condition' if answer==z.unsat else 'different-condition' if answer==z.sat else 'comparison-unknown'
            (out/('condition-'+str(ri)+'.smt2')).write_text(solver.to_smt2())
            record={'name':row['name'],'status':status,'comparison':str(answer),**result['summary']}
            if answer==z.sat:record['countermodel']=str(solver.model())
        except Incomplete as err:record={'name':row['name'],'status':'incomplete','reason':str(err)}
        rows.append(record)
        if len(rows)%32==0:print(json.dumps({'contracts':len(rows)}),flush=True)
    counts={s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})}
    result={'rows':rows,'contracts':len(rows),'statuses':counts,'z3':z.get_version_string(),'scope':'Self-built generic SMT WP/QE baseline, not an author-tool reproduction. One pass timings are diagnostic only.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-import-generic.py','guard-import-generic-plan.md','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
