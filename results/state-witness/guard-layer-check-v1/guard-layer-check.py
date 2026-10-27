"""Check finite-horizon recurrence equivalence using independent array effects.

This checks exactness within the shared parsed model; it is not a mechanization
of the WebAssembly specification or a general completeness theorem.
"""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=load('witness','guard-witness.py');c=load('checker','guard-table-check.py');z=c.z
def main(source,out,maxcells):
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((source/'manifest.json').read_text());rows=[]
    for row in manifest['rows']:
        model=w.g.parse(k.p.read(source/row['source']))
        if len(model['cells'])>maxcells:rows.append({'name':row['name'],'status':'skipped-cell-budget','cells':len(model['cells'])});continue
        prepared=w.prepare(model,row['left'],row['right']);states=prepared['proof']['states'];layers=prepared['layers']
        lookup={(tuple(s['left']),tuple(s['right'])):i for i,s in enumerate(states)};checks=[];started=time.perf_counter()
        # Include the stable last-to-last step as well as every strengthening step.
        for li in range(1,len(layers)+1):
            previous=layers[li-1];following=layers[min(li,len(layers)-1)]
            for si,state in enumerate(states):
                array=z.Array('initial',z.IntSort(),z.IntSort());obligations=[]
                for action in model['actions']:
                    if action['readonly']:continue
                    left,lt,ls=c.execute(model,state['left'],action,array);right,rt,rs=c.execute(model,state['right'],action,array)
                    post=[] if left==right else previous[lookup[(left,right)]]
                    obligations.append(z.And(z.BoolVal(lt==rt),ls==rs,c.condition(post,ls)))
                rhs=z.And(*obligations);lhs=c.condition(following[si],array)
                solver=z.Solver();solver.set(timeout=5000);solver.add(c.domain(model,array),lhs!=rhs);answer=solver.check()
                checks.append({'layer':li,'state':si,'answer':str(answer)})
                assert answer!=z.sat,(row['name'],li,si,'recurrence mismatch')
        rows.append({'name':row['name'],'status':'verified' if all(q['answer']=='unsat' for q in checks) else 'solver-unknown',
          'layers':len(layers),'checks':checks,'seconds':time.perf_counter()-started})
    result={'rows':rows,'verifiedCertificates':sum(r['status']=='verified' for r in rows),
      'skippedByCellBudget':sum(r['status']=='skipped-cell-budget' for r in rows),'solverUnknownCases':sum(r['status']=='solver-unknown' for r in rows),
      'unsatEquivalenceObligations':sum(q['answer']=='unsat' for r in rows for q in r.get('checks',[])),
      'maxCells':maxcells,'z3':z.get_version_string(),'scope':'Each finite-horizon recurrence and stable step in a shared parsed model, independently encoded array effects; not a Wasm metatheorem.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-layer-check.py','guard-witness.py','guard-table-check.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--max-cells',type=int,default=32);v=p.parse_args();main(v.source,v.out,v.max_cells)
