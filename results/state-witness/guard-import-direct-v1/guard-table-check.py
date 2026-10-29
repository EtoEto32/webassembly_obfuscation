"""Independent array semantics for bulk memory/table guard certificates.

The AST profile/parser is shared. Effects use SMT Store/Select rather than the
generator's copy maps. Cell sorts are constrained for concrete countermodels.
"""
import argparse,copy,hashlib,importlib.util,json,shutil,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('table_guard',HERE/'guard-table.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
sys.path.insert(0,str(ROOT/'.tools/encoding-synthesis-python'));import z3 as z

def condition(guard,array):
    if guard is None:return z.BoolVal(False)
    def value(t):return z.IntVal(t[1]) if t[0]=='c' else z.Select(array,t[1])
    return z.And(*[value(a)==value(b) for a,b in guard])

def domain(model,array):
    rules=[]
    for c in model['cells']:
        v=z.Select(array,c);resource=model['resources'][c//g.BASE]
        rules.append(z.And(v>=0,v<=255) if resource['kind']=='memory' else z.And(v>=256,v<=256+model['functions']))
    return z.And(*rules)

def execute(model,alive,action,array):
    flags=list(alive);store=array;trapped=False
    for op in action['ops']:
        kind=op['kind']
        if kind=='drop':flags[op['segment']]=False;continue
        r,d,n=op['resource'],op['dst'],op['length'];bound=model['resources'][r]['length']
        if d>bound or n>bound-d:trapped=True;break
        if kind=='init':
            data=model['segments'][op['segment']]['values'] if flags[op['segment']] else []
            src=op['src']
            if src>len(data) or n>len(data)-src:trapped=True;break
            values=[z.IntVal(x) for x in data[src:src+n]]
        elif kind=='copy':
            src,sr=op['src'],op['sourceResource'];bound=model['resources'][sr]['length']
            if src>bound or n>bound-src:trapped=True;break
            before=store;values=[z.Select(before,sr*g.BASE+src+i) for i in range(n)]
        elif kind=='fill':values=[z.IntVal(op['value']) for _ in range(n)]
        else:raise ValueError(kind)
        for i,value in enumerate(values):store=z.Store(store,r*g.BASE+d+i,value)
    return tuple(flags),trapped,store

def check(model,proof):
    states=proof['states'];assert states and states[0]['guard']==proof['guard']
    lookup={(tuple(s['left']),tuple(s['right'])):s for s in states};assert len(lookup)==len(states)
    checks=[]
    for si,state in enumerate(states):
        for side in ('left','right'):
            assert len(state[side])==len(model['segments'])
            assert all(not v or s['initialLive'] for v,s in zip(state[side],model['segments']))
        for action in model['actions']:
            if action['readonly']:continue
            array=z.Array('initial',z.IntSort(),z.IntSort())
            left,lt,lstore=execute(model,state['left'],action,array);right,rt,rstore=execute(model,state['right'],action,array)
            target=lookup.get((left,right))
            if left!=right and target is None:raise ValueError('missing successor certificate')
            postguard=[] if left==right else target['guard']
            obligation=z.And(z.BoolVal(lt==rt),lstore==rstore,condition(postguard,lstore))
            solver=z.Solver();solver.set(timeout=5000);solver.add(domain(model,array),condition(state['guard'],array),z.Not(obligation))
            answer=solver.check();item={'state':si,'api':action['name'],'answer':str(answer)}
            if answer==z.sat:
                m=solver.model();item['counterexampleCells']={str(i):m.eval(z.Select(array,i),model_completion=True).as_long() for i in model['cells']}
                item['failed']={'outcome':lt!=rt,'store':not z.is_true(m.eval(lstore==rstore,model_completion=True)),
                                'postcondition':not z.is_true(m.eval(condition(postguard,lstore),model_completion=True))}
            checks.append(item)
    return checks

def main(source,out,spec):
    out.mkdir(parents=True,exist_ok=False)
    sourcefile=source/('manifest.json' if (source/'manifest.json').exists() else 'results.json')
    manifest=json.loads(sourcefile.read_text());rows=[]
    for ri,row in enumerate(manifest['rows']):
        proof=row['proof']
        if proof['status']=='unsupported':continue
        src=(spec if spec else source)/row['source'];model=g.parse(k.p.read(src))
        checks=check(model,proof);assert all(c['answer']=='unsat' for c in checks),(ri,checks)
        mutants=[]
        if proof['guard']:
            for mode in ('remove-all','remove-last'):
                changed=copy.deepcopy(proof);weak=[] if mode=='remove-all' else changed['guard'][:-1]
                changed['guard']=weak;changed['states'][0]['guard']=weak
                bad=check(model,changed);assert any(c['answer']=='sat' for c in bad),(ri,mode,bad)
                mutants.append({'mode':mode,'checks':bad})
        rows.append({'sourceRow':ri,'source':row['source'],'name':row.get('name'), 'status':proof['status'],'checks':checks,'weakenedControls':mutants})
    result={'z3':z.get_version_string(),'rows':rows,'checkedCertificates':len(rows),
      'unsatObligations':sum(len(r['checks']) for r in rows),'rejectedWeakenings':sum(len(r['weakenedControls']) for r in rows),
      'sourceManifestSha256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
      'scope':'Shared parser; independent typed-domain array effects; sufficient inductive certificates, not weakestness or reachable-state proof.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-table-check.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    print(json.dumps({k:v for k,v in result.items() if isinstance(v,(str,int))}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('--spec',type=Path);v=p.parse_args();main(v.source,v.out,v.spec)
