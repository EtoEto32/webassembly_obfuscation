"""SMT check of emitted guards using array semantics, not the copy-expression map."""
import argparse,copy,hashlib,importlib.util,json,shutil,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('guard_analysis',HERE/'guard-analysis.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
sys.path.insert(0,str(ROOT/'.tools/encoding-synthesis-python'));import z3 as z

def condition(guard,array):
    if guard is None:return z.BoolVal(False)
    def value(t):return z.BitVecVal(t[1],8) if t[0]=='c' else z.Select(array,z.BitVecVal(t[1],32))
    return z.And(*[value(a)==value(b) for a,b in guard])

def execute(model,alive,action,array):
    flags=list(alive);memory=array;trapped=False
    for op in action['ops']:
        name=op[0]
        if name=='data.drop':flags[op[1]]=False;continue
        _,dst,src,n,index=op
        if dst>model['size'] or n>model['size']-dst:trapped=True;break
        if name=='memory.init':
            data=model['segments'][index]['data'] if flags[index] else b''
            if src>len(data) or n>len(data)-src:trapped=True;break
            values=[z.BitVecVal(x,8) for x in data[src:src+n]]
        elif name=='memory.copy':
            if src>model['size'] or n>model['size']-src:trapped=True;break
            before=memory;values=[z.Select(before,z.BitVecVal(src+i,32)) for i in range(n)]
        elif name=='memory.fill':values=[z.BitVecVal(src&255,8) for _ in range(n)]
        else:raise ValueError(name)
        for i,v in enumerate(values):memory=z.Store(memory,z.BitVecVal(dst+i,32),v)
    return tuple(flags),trapped,memory

def check(model,proof):
    states=proof['states'];assert states[0]['guard']==proof['guard']
    lookup={(tuple(s['left']),tuple(s['right'])):s for s in states};checks=[]
    for si,state in enumerate(states):
        for action in model['actions']:
            if action['readonly']:continue # equal full arrays imply all load8 values/traps
            array=z.Array('initial',z.BitVecSort(32),z.BitVecSort(8));left,lt,lmem=execute(model,state['left'],action,array);right,rt,rmem=execute(model,state['right'],action,array)
            target=lookup.get((left,right));postguard=[] if left==right else target['guard'] if target else None
            if left!=right and target is None:raise ValueError('missing successor certificate')
            obligation=z.And(z.BoolVal(lt==rt),lmem==rmem,condition(postguard,lmem))
            solver=z.Solver();solver.set(timeout=5000);solver.add(condition(state['guard'],array),z.Not(obligation));answer=solver.check()
            item={'state':si,'api':action['name'],'answer':str(answer)}
            if answer==z.sat:
                m=solver.model();item['counterexampleCells']={str(i):m.eval(z.Select(array,z.BitVecVal(i,32)),model_completion=True).as_long() for i in model['cells']}
                item['failed']={'outcome':lt!=rt,'memory':not z.is_true(m.eval(lmem==rmem,model_completion=True)),
                                'postcondition':not z.is_true(m.eval(condition(postguard,lmem),model_completion=True))}
            checks.append(item)
    return checks

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((source/'manifest.json').read_text());rows=[]
    for row in manifest['rows']:
        # Controls include a raw source. Measured validation only includes a prepared
        # module, so remove only the explicit preparation helper exports before parse.
        src=source/row.get('source',row['prepared']);module=k.p.read(src)
        module=[x for x in module if not (isinstance(x,list) and x and x[0]=='export' and x[1].startswith('"__guard_drop_'))]
        model=g.parse(module);proof=row['proof'];checks=check(model,proof);assert all(c['answer']=='unsat' for c in checks),(row['name'],checks)
        mutants=[]
        if proof['guard']:
            for mode in ('remove-all','remove-last'):
                changed=copy.deepcopy(proof);weak=[] if mode=='remove-all' else changed['guard'][:-1]
                changed['guard']=weak;changed['states'][0]['guard']=weak
                bad=check(model,changed);assert any(c['answer']=='sat' for c in bad),(row['name'],mode,bad)
                mutants.append({'mode':mode,'checks':bad})
        rows.append({'name':row['name'],'status':proof['status'],'checks':checks,'weakenedControls':mutants})
    result={'z3':z.get_version_string(),'rows':rows,'checkedCertificates':len(rows),
      'unsatObligations':sum(len(r['checks']) for r in rows),'rejectedWeakenings':sum(len(r['weakenedControls']) for r in rows),
      'sourceManifestSha256':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
      'scope':'Shared parser, independent array effect encoding. Sufficient inductive certificates, not a machine-checked metatheorem or weakestness proof.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for n in ('guard-check.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    print(json.dumps({k:v for k,v in result.items() if isinstance(v,(str,int))}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.out)
