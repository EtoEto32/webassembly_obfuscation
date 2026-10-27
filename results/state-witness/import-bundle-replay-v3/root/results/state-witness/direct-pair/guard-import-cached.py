"""General SMT baseline with support slicing, cached WP/QE, incremental checks."""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('uncached_smt',HERE/'guard-import-generic.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
q=base.q;z=base.z;Incomplete=base.Incomplete

def support(formula):
    seen=set();free=set();todo=[formula]
    while todo:
        node=todo.pop();ident=node.get_id()
        if ident in seen:continue
        seen.add(ident)
        if z.is_const(node) and node.decl().kind()==z.Z3_OP_UNINTERPRETED:free.add(ident)
        todo.extend(node.children())
    return free

def solve(model,left_flags,right_flags,contract,protocol,timeout=5000,iterations=1024):
    started=time.perf_counter();left,right,variables,domain=base.predicate_environment(model)
    states=[(tuple(left_flags),tuple(right_flags))];lookup={states[0]:0};edges=[]
    observed=set(model['resources']) if contract=='full' else set(model['publicResources']) if contract=='public' else set()
    for pair in states:
        if len(states)>1024:raise Incomplete('state-limit')
        row=[]
        for action in model['actions']:
            edge=base.transition(model,pair,action,left,right,variables)
            if edge['target'] not in lookup:lookup[edge['target']]=len(states);states.append(edge['target'])
            edge['local'].extend(z.Select(edge['left']['array'],cell)==z.Select(edge['right']['array'],cell) for cell in model['cells'] if cell//q.i.g.BASE in observed)
            edge['local']=z.simplify(z.And(*edge['local']))
            edge['replace']=[(v,z.simplify(z.Select(edge[side]['array'],cell))) for (side,cell),v in variables.items()]
            edge['cache']={};row.append(edge)
        edges.append(row)
    solver=z.Solver();solver.set(timeout=timeout);solver.add(domain)
    prepared=time.perf_counter()-started;guards=[z.BoolVal(True) for _ in states];qe_calls=queries=hits=0;trace=[]
    for iteration in range(1,iterations+1):
        new=[];support_cache={}
        for row in edges:
            formulas=[]
            for edge in row:
                successor=z.BoolVal(True) if protocol=='terminal' and edge['bothTrap'] else guards[lookup[edge['target']]]
                # The full SMT text is a collision-free key; no dependence on recycled AST IDs.
                key=successor.sexpr()
                if key in edge['cache']:formula=edge['cache'][key];hits+=1
                else:
                    if key not in support_cache:support_cache[key]=support(successor)
                    replace=[(v,value) for v,value in edge['replace'] if v.get_id() in support_cache[key]]
                    if replace:successor=z.substitute(successor,*replace)
                    formula=z.simplify(z.And(edge['local'],successor))
                    if edge['inputs']:
                        quantified=z.simplify(z.ForAll(edge['inputs'],z.Implies(edge['inputDomain'],formula)))
                        if z.is_quantifier(quantified):
                            try:formula=z.TryFor(z.Tactic('qe'),timeout)(quantified).as_expr()
                            except z.Z3Exception as err:raise Incomplete('qe-failure: '+str(err))
                            qe_calls+=1
                        else:formula=quantified
                    formula=z.simplify(formula);edge['cache'][key]=formula
                formulas.append(formula)
            new.append(z.simplify(z.And(*formulas)))
        equal=True
        for a,b in zip(guards,new):
            if z.eq(a,b):continue
            solver.push();solver.add(a!=b);answer=solver.check();queries+=1
            if answer==z.unknown:raise Incomplete('equivalence-unknown: '+solver.reason_unknown())
            if answer==z.sat:equal=False
            solver.pop()
        guards=new;trace.append({'iteration':iteration,'totalSmtCharacters':sum(len(f.sexpr()) for f in guards),'fixed':equal})
        if equal:break
    else:raise Incomplete('iteration-limit')
    common=base.substitute(guards[0],variables,left,left)
    return {'formula':common,'variables':variables,'left':left,'right':right,'domain':domain,'guards':guards,
        'summary':{'iterations':iteration,'states':len(states),'qeCalls':qe_calls,'equivalenceQueries':queries,'cacheHits':hits,'preparationSeconds':prepared,
                   'seconds':time.perf_counter()-started,'trace':trace,'smt':common.sexpr()}}

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for ri,row in enumerate(json.loads((source/'manifest.json').read_text())['rows']):
        proof=row['proof'];summaries={(s['module'],s['field']):{k:s[k] for k in ('reads','writes')} for s in proof['hostSummaries']}
        model=q.i.parse(q.i.k.p.read(source/row['source']),summaries,proof.get('continuationOffsets'))
        try:
            r=solve(model,row['left'],row['right'],proof['contract'],proof['protocol']);solver=z.Solver();solver.set(timeout=5000)
            solver.add(r['domain'],r['formula']!=q.a.a.predicate(proof['guard'],r['left'],r['left']));answer=solver.check()
            (out/('condition-'+str(ri)+'.smt2')).write_text(solver.to_smt2())
            record={'name':row['name'],'status':'same-condition' if answer==z.unsat else 'different-condition' if answer==z.sat else 'comparison-unknown',**r['summary']}
        except Incomplete as err:record={'name':row['name'],'status':'incomplete','reason':str(err)}
        rows.append(record)
    result={'rows':rows,'contracts':len(rows),'statuses':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},'z3':z.get_version_string()}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-import-cached.py','guard-import-cached-plan.md','guard-import-generic.py','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
