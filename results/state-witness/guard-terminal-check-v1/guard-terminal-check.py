"""Check a restricted collapse lemma with independent symbolic array effects."""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
f=load('fast','guard-terminal-fast.py');a=load('symbolic','guard-project-check.py');z=a.z

def check(source):
    model=f.c.parse(k.p.read(source));flags=[]
    for side in ('left','right'):
        flags.append([z.Bool(side+str(i)) if s['initialLive'] else z.BoolVal(False) for i,s in enumerate(model['segments'])])
    common_drops=[z.Bool('drop'+str(i)) for i in range(len(model['segments']))];array=z.Array('common',z.IntSort(),z.IntSort());checks=[]
    for action in model['actions']:
        lf,lr,lm=a.execute(model,flags[0],action,array);rf,rr,rm=a.execute(model,flags[1],action,array)
        dl=[z.And(v,z.Not(d)) for v,d in zip(flags[0],common_drops)];dr=[z.And(v,z.Not(d)) for v,d in zip(flags[1],common_drops)]
        _,lrd,_=a.execute(model,dl,action,array);_,rrd,_=a.execute(model,dr,action,array)
        drops={o['segment'] for o in action['ops'] if o['kind']=='drop'}
        updates=z.And(*[new==(z.BoolVal(False) if i in drops else old) for original,following in zip(flags,(lf,rf)) for i,(old,new) in enumerate(zip(original,following))])
        properties={'common-drop-outcome':z.Implies(lr==rr,lrd==rrd),'normal-store':z.Implies(z.And(lr,rr),lm==rm),'normal-flags':z.Implies(z.And(lr,rr),updates)}
        for name,prop in properties.items():
            solver=z.Solver();solver.set(timeout=5000);solver.add(a.c.domain(model,array),z.Not(prop));answer=solver.check()
            assert answer!=z.sat,(str(source),action['name'],name,str(solver.model()) if answer==z.sat else '')
            checks.append({'api':action['name'],'property':name,'answer':str(answer)})
    return {'source':str(source),'checks':checks}

def main(witness,contracts,out):
    out.mkdir(parents=True,exist_ok=False);paths=[witness/r['source'] for r in json.loads((witness/'manifest.json').read_text())['rows']]
    paths+=sorted({contracts/r['source'] for r in json.loads((contracts/'manifest.json').read_text())['rows']});started=time.perf_counter();rows=[check(src) for src in paths]
    result={'rows':rows,'modules':len(rows),'unsat':sum(x['answer']=='unsat' for r in rows for x in r['checks']),'unknown':sum(x['answer']=='unknown' for r in rows for x in r['checks']),
      'seconds':time.perf_counter()-started,'z3':z.get_version_string(),'scope':'All segment flags and common drop sets per accepted module; symbolic array effects. Read-byte input cases rely on equal memory/capacity and the separate argument in the lemma.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-terminal-check.py','guard-terminal-fast.py','guard-contract.py','guard-project-check.py','guard-project.py','guard-witness.py','guard-table-check.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('witness','contracts','out'):p.add_argument(n,type=Path)
    v=p.parse_args();main(v.witness,v.contracts,v.out)
