"""SMT-check projection commutation for arbitrary segment flags and stores."""
import argparse,hashlib,importlib.util,json,shutil
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('projection','guard-project.py');c=load('checker','guard-table-check.py');z=c.z
BASE=1<<32
def execute(model,flags,action,array):
    flags=flags.copy();store=array;running=z.BoolVal(True)
    for op in action['ops']:
        if op['kind']=='drop':
            si=op['segment'];flags[si]=z.If(running,z.BoolVal(False),flags[si]);continue
        r,d,n=op['resource'],op['dst'],op['length'];limit=model['resources'][r]['length'];valid=z.BoolVal(d<=limit and n<=limit-d)
        if op['kind']=='init':
            si,src=op['segment'],op['src'];data=model['segments'][si]['values']
            valid=z.And(valid,z.If(flags[si],z.BoolVal(src<=len(data) and n<=len(data)-src),z.BoolVal(src==0 and n==0)))
            # Values outside a live segment are irrelevant: valid is false.
            vals=[z.IntVal(data[src+i] if src+i<len(data) else 0) for i in range(n)]
        elif op['kind']=='copy':
            sr,src=op['sourceResource'],op['src'];limit=model['resources'][sr]['length']
            valid=z.And(valid,z.BoolVal(src<=limit and n<=limit-src));before=store;vals=[z.Select(before,sr*BASE+src+i) for i in range(n)]
        else:vals=[z.IntVal(op['value'])]*n
        after=store
        for i,v in enumerate(vals):after=z.Store(after,r*BASE+d+i,v)
        store=z.If(z.And(running,valid),after,store);running=z.And(running,valid)
    return flags,running,store
def check(source):
    model=p.w.g.parse(k.p.read(source));initial=[s['initialLive'] for s in model['segments']]
    reduced,_,_,kept=p.project(model,initial,initial)
    flags=[z.Bool('segment_'+str(i)) if s['initialLive'] else z.BoolVal(False) for i,s in enumerate(model['segments'])]
    checks=[]
    for original,projected in zip(model['actions'],reduced['actions']):
        if original['readonly']:continue
        array=z.Array('initial',z.IntSort(),z.IntSort());af,ar,am=execute(model,flags,original,array)
        bf,br,bm=execute(reduced,[flags[i] for i in kept],projected,array)
        equivalent=z.And(ar==br,am==bm,*[af[old]==bf[new] for new,old in enumerate(kept)])
        solver=z.Solver();solver.set(timeout=5000);solver.add(c.domain(model,array),z.Not(equivalent));answer=solver.check()
        assert answer!=z.sat,(str(source),original['name'],'projection counterexample')
        checks.append({'api':original['name'],'answer':str(answer)})
    return {'source':str(source),'kept':kept,'segmentsBefore':len(flags),'checks':checks,
      'status':'verified' if all(x['answer']=='unsat' for x in checks) else 'solver-unknown'}
def main(witness,projection,out):
    out.mkdir(parents=True,exist_ok=False);sources=[witness/r['source'] for r in json.loads((witness/'manifest.json').read_text())['rows']]
    sources+=sorted(projection.glob('projection-??.wasm'));rows=[check(src) for src in sources]
    result={'rows':rows,'verifiedModules':sum(r['status']=='verified' for r in rows),'solverUnknownModules':sum(r['status']=='solver-unknown' for r in rows),
      'unsatCommutationObligations':sum(q['answer']=='unsat' for r in rows for q in r['checks']),
      'z3':z.get_version_string(),'scope':'Symbolic segment flags, typed stores, independent array effects; parser shared; erased segment state is outside the chosen API/store observation contract.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-project-check.py','guard-project.py','guard-witness.py','guard-table-check.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    a=argparse.ArgumentParser()
    for name in ('witness','projection','out'):a.add_argument(name,type=Path)
    v=a.parse_args();main(v.witness,v.projection,v.out)
