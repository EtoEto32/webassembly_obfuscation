"""Independent two-array recurrence checks for chosen observation contracts."""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=load('contract','guard-contract.py');a=load('array_checker','guard-table-check.py');z=a.z
def predicate(guard,left,right):
    if guard is None:return z.BoolVal(False)
    def value(t):return z.IntVal(t[1]) if t[0]=='c' else z.Select(right if t[0]=='r' else left,t[1])
    return z.And(*[value(x)==value(y) for x,y in guard])
def arrays(model):
    shared=z.Array('untouched',z.IntSort(),z.IntSort());left=right=shared;domain=[]
    for i in model['cells']:
        l,r=z.Int('left_'+str(i)),z.Int('right_'+str(i));left=z.Store(left,i,l);right=z.Store(right,i,r)
        kind=model['resources'][i//c.g.BASE]['kind'];lo,hi=(0,255) if kind=='memory' else (256,256+model['functions'])
        domain.extend([z.And(l>=lo,l<=hi),z.And(r>=lo,r<=hi)])
    return left,right,z.And(*domain)
def check(model,prepared):
    proof=prepared['proof'];states=proof['states'];layers=prepared['layers'];lookup={(tuple(s['left']),tuple(s['right'])):i for i,s in enumerate(states)}
    left,right,domain=arrays(model);visible=[i for i in model['cells'] if i//c.g.BASE in proof['observedResources']];checks=[]
    for li in range(1,len(layers)+1):
        previous=layers[li-1];following=layers[min(li,len(layers)-1)]
        for si,state in enumerate(states):
            allactions=[]
            for action in model['actions']:
                lf,lt,lm=a.execute(model,state['left'],action,left);rf,rt,rm=a.execute(model,state['right'],action,right)
                local=[z.BoolVal(lt==rt)]+[z.Select(lm,i)==z.Select(rm,i) for i in visible]
                if action['observation']=='read-byte':local += [z.Select(left,i)==z.Select(right,i) for i in model['cells'] if i<c.g.BASE]
                allactions.append(z.And(*local,predicate(previous[lookup[(lf,rf)]],lm,rm)))
            solver=z.Solver();solver.set(timeout=5000);solver.add(domain,predicate(following[si],left,right)!=z.And(*allactions));answer=solver.check()
            assert answer!=z.sat,('recurrence mismatch',proof['contract'],li,si)
            checks.append({'layer':li,'state':si,'answer':str(answer)})
    common=z.Array('common',z.IntSort(),z.IntSort());solver=z.Solver();solver.set(timeout=5000)
    solver.add(a.domain(model,common),predicate(layers[-1][0],common,common)!=predicate(proof['guard'],common,common));answer=solver.check()
    assert answer!=z.sat,'initial equality projection mismatch';checks.append({'initialCommonStore':True,'answer':str(answer)})
    return checks
def aligned_mutant(prepared):
    states=prepared['proof']['states'];edges=[[] if s['left']==s['right'] else row for s,row in zip(states,prepared['edges'])];guards=[frozenset() for _ in states]
    for _ in range(1024):
        new=[c.g.g.combine(*[c.g.g.combine(e['local'],c.pullback(guards[e['target']],e['left'],e['right'])) for e in row]) for row in edges]
        if new==guards:break
        guards=new
    else:raise AssertionError('mutant bound')
    result=guards[0]
    return c.g.g.canonical([(('m',x[1]) if x[0] in ('l','r') else x,('m',y[1]) if y[0] in ('l','r') else y) for x,y in result]) if result is not None else None
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((source/'manifest.json').read_text());rows=[];mutant_misses=0
    for row in manifest['rows']:
        model=c.parse(k.p.read(source/row['source']));prepared=c.prepare(model,row['left'],row['right'],row['proof']['contract']);assert json.loads(json.dumps(prepared['proof']))==row['proof']
        started=time.perf_counter();checks=check(model,prepared);mutant=aligned_mutant(prepared);misses=[]
        for si,s in enumerate(row['samples']):
            values={i:0 if i<c.g.BASE else 256 for i in model['cells']};values.update(dict(s['patches']))
            if s['witness'] and c.holds(mutant,values,values):misses.append(si)
        mutant_misses+=len(misses);rows.append({'name':row['name'],'status':'verified' if all(q['answer']=='unsat' for q in checks) else 'solver-unknown',
          'checks':checks,'seconds':time.perf_counter()-started,'earlyAlignedMutantGuard':c.serial(mutant),'mutantFalseEqualSamples':misses})
    result={'rows':rows,'verifiedContracts':sum(r['status']=='verified' for r in rows),'solverUnknownContracts':sum(r['status']=='solver-unknown' for r in rows),
      'unsatObligations':sum(q['answer']=='unsat' for r in rows for q in r['checks']),'earlyAlignedMutantMisses':mutant_misses,
      'scope':'Independent two-array effects with shared untouched cells; all layers and common-initial-store projection; shared parser/profile; not a Wasm metatheorem.','z3':z.get_version_string()}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-contract-check.py','guard-contract.py','guard-table-check.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.out)
