"""Independent arrays plus quantified host assignments for each recurrence."""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
e=load('environment','guard-environment.py');a=load('arrays','guard-contract-check.py');z=a.z

def arrays(model):
    common=z.Array('untouched',z.IntSort(),z.IntSort());left=right=common;domain=[]
    for cell in model['cells']:
        l,r=z.Int('left'+str(cell)),z.Int('right'+str(cell));left=z.Store(left,cell,l);right=z.Store(right,cell,r)
        domain.extend([z.And(v>=0,v<=255) if cell<e.c.g.BASE else v>=256 for v in (l,r)])
    return left,right,z.And(*domain)

def environment(model,relation,left,right):
    variables=[];domain=[];la,ra=left,right
    for cell in model['cells']:
        if cell//e.c.g.BASE not in model['publicResources']:continue
        value=z.Int('host'+str(cell));variables.append(value);domain.append(z.And(value>=0,value<=255) if cell<e.c.g.BASE else value>=256)
        la=z.Store(la,cell,value);ra=z.Store(ra,cell,value)
    body=a.predicate(relation,la,ra)
    return z.ForAll(variables,z.Implies(z.And(*domain),body)) if variables else body

def check(model,prepared):
    proof=prepared['proof'];states=proof['states'];layers=prepared['layers'];lookup={(tuple(v['left']),tuple(v['right'])):i for i,v in enumerate(states)}
    left,right,domain=arrays(model);visible=[i for i in model['cells'] if i//e.c.g.BASE in proof['observedResources']];checks=[]
    for li in range(1,len(layers)+1):
        previous=layers[li-1];following=layers[min(li,len(layers)-1)]
        for si,state in enumerate(states):
            actions=[environment(model,previous[si],left,right)]
            for action in model['actions']:
                lf,lt,lm=a.a.execute(model,state['left'],action,left);rf,rt,rm=a.a.execute(model,state['right'],action,right)
                local=[z.BoolVal(lt==rt)]+[z.Select(lm,i)==z.Select(rm,i) for i in visible]
                if action['observation']=='read-byte':local += [z.Select(left,i)==z.Select(right,i) for i in model['cells'] if i<e.c.g.BASE]
                stops=proof['protocol']=='terminal' and ((lt and rt) or action['observation']=='read-byte' and model['resources'][0]['length']==0)
                if not stops:local.append(a.predicate(previous[lookup[(lf,rf)]],lm,rm))
                actions.append(z.And(*local))
            solver=z.Solver();solver.set(timeout=5000);solver.add(domain,a.predicate(following[si],left,right)!=z.And(*actions));answer=solver.check()
            if answer==z.sat:raise AssertionError(('recurrence',li,si,str(solver.model())))
            checks.append({'layer':li,'state':si,'answer':str(answer),'reason':solver.reason_unknown() if answer==z.unknown else None})
    return checks

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[];cache={}
    try:
        for row in json.loads((source/'manifest.json').read_text())['rows']:
            if row['source'] not in cache:cache[row['source']]=e.c.parse(e.k.p.read(source/row['source']))
            model=cache[row['source']];prepared=e.prepare(model,row['left'],row['right'],row['proof']['contract'],row['proof']['protocol']);assert json.loads(json.dumps(prepared['proof']))==row['proof']
            started=time.perf_counter();checks=check(model,prepared);rows.append({'name':row['name'],'checks':checks,'seconds':time.perf_counter()-started})
            if len(rows)%96==0:print(json.dumps({'contracts':len(rows)}),flush=True)
        result={'rows':rows,'contracts':len(rows),'unsat':sum(v['answer']=='unsat' for r in rows for v in r['checks']),
            'unknown':sum(v['answer']=='unknown' for r in rows for v in r['checks']),'z3':z.get_version_string(),
            'scope':'Independent array semantics and universally quantified common public assignments, shared parser; table identity domain unbounded >=256. Not full Wasm semantics proof.'}
        (out/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
    except Exception as err:(out/'failure.json').write_text(json.dumps({'reason':repr(err),'rows':rows},indent=2));raise
    finally:
        for name in ('guard-environment-check.py','guard-environment.py','guard-contract-check.py','guard-table-check.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
        (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2))

if __name__=='__main__':
    a0=argparse.ArgumentParser();a0.add_argument('source',type=Path);a0.add_argument('out',type=Path);v=a0.parse_args();main(v.source,v.out)
