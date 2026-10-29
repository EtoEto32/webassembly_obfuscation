"""Independent array recurrence with terminal trap transitions."""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('protocol','guard-protocol.py');a=load('checker','guard-contract-check.py');z=a.z

def check(model,prepared):
    proof=prepared['proof'];states=proof['states'];layers=prepared['layers'];lookup={(tuple(s['left']),tuple(s['right'])):i for i,s in enumerate(states)}
    left,right,domain=a.arrays(model);visible=[i for i in model['cells'] if i//p.c.g.BASE in proof['observedResources']];checks=[]
    for li in range(1,len(layers)+1):
        previous=layers[li-1];following=layers[min(li,len(layers)-1)]
        for si,state in enumerate(states):
            actions=[]
            for action in model['actions']:
                lf,lt,lm=a.a.execute(model,state['left'],action,left);rf,rt,rm=a.a.execute(model,state['right'],action,right)
                local=[z.BoolVal(lt==rt)]+[z.Select(lm,i)==z.Select(rm,i) for i in visible]
                if action['observation']=='read-byte':local += [z.Select(left,i)==z.Select(right,i) for i in model['cells'] if i<p.c.g.BASE]
                # Independent stop predicate; do not consume producer edges.
                stops=(lt and rt) or action['observation']=='read-byte' and model['resources'][0]['length']==0
                if not stops:local.append(a.predicate(previous[lookup[(lf,rf)]],lm,rm))
                actions.append(z.And(*local))
            solver=z.Solver();solver.set(timeout=5000);solver.add(domain,a.predicate(following[si],left,right)!=z.And(*actions));answer=solver.check()
            assert answer!=z.sat,('recurrence mismatch',proof['contract'],li,si);checks.append({'layer':li,'state':si,'answer':str(answer)})
    common=z.Array('common',z.IntSort(),z.IntSort());solver=z.Solver();solver.set(timeout=5000)
    solver.add(a.a.domain(model,common),a.predicate(layers[-1][0],common,common)!=a.predicate(proof['guard'],common,common));answer=solver.check()
    assert answer!=z.sat,'common initial projection';checks.append({'initialCommonStore':True,'answer':str(answer)});return checks

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for row in json.loads((source/'manifest.json').read_text())['rows']:
        model=p.c.parse(k.p.read(source/row['source']));prepared=p.prepare(model,row['left'],row['right'],row['proof']['contract']);assert json.loads(json.dumps(prepared['proof']))==row['proof']
        start=time.perf_counter();checks=check(model,prepared);rows.append({'name':row['name'],'checks':checks,'seconds':time.perf_counter()-start})
    result={'rows':rows,'contracts':len(rows),'unsat':sum(x['answer']=='unsat' for r in rows for x in r['checks']),
       'unknown':sum(x['answer']=='unknown' for r in rows for x in r['checks']),'z3':z.get_version_string(),'scope':'Terminal protocol recurrence; independent arrays and stop predicate, shared parser. Not a Wasm metatheorem.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-protocol-check.py','guard-protocol.py','guard-contract-check.py','guard-contract.py','guard-table-check.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    q=argparse.ArgumentParser();q.add_argument('source',type=Path);q.add_argument('out',type=Path);v=q.parse_args();main(v.source,v.out)
