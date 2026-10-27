"""Independent symbolic counterexample search for the two-value candidate basis."""
import argparse,hashlib,importlib.util,itertools,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('basis_check',HERE/'guard-import-check.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q);z=q.z


def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for sort in ('byte','reference'):
        base,alt=(0,1) if sort=='byte' else (256,257)
        left=[z.Int(sort+'_l'+str(c)) for c in range(3)];right=[z.Int(sort+'_r'+str(c)) for c in range(3)];host=[z.Int(sort+'_h'+str(c)) for c in range(2)]
        typed=lambda x:z.And(x>=0,x<=255) if sort=='byte' else x>=256
        domain=z.And(*[typed(v) for v in left+right+host]);terms=[(side,c) for side in ('l','r') for c in range(3)]+[('c',base),('c',alt),('c',alt+1)]
        def predicate(atom,assignment):
            def term(t):
                side,c=t
                if side=='c':return z.IntVal(c)
                if c<2:return assignment[c]
                return (left if side=='l' else right)[c]
            return term(atom[0])==term(atom[1])
        candidates=[[z.IntVal(base),z.IntVal(base)],[z.IntVal(alt),z.IntVal(base)],[z.IntVal(base),z.IntVal(alt)]]
        for atom in itertools.combinations_with_replacement(terms,2):
            solver=z.Solver();solver.set(timeout=5000);solver.add(domain,*[predicate(atom,a) for a in candidates],z.Not(predicate(atom,host)));answer=solver.check()
            rows.append({'sort':sort,'atom':atom,'answer':str(answer)});assert answer==z.unsat,(atom,answer)
    # A disjunction needs both cells changed; none of the three candidates fails.
    relation=lambda a:a[0]==0 or a[1]==0
    general={'relation':'x == 0 OR y == 0','candidates':[[0,0],[1,0],[0,1]],'missed':[1,1]}
    assert all(relation(a) for a in general['candidates']) and not relation(general['missed'])
    result={'obligations':rows,'unsat':len(rows),'unknown':0,'generalBooleanCounterexample':general,'z3':z.get_version_string(),
        'scope':'Atomic byte/reference equalities with two writable and one private cell; arbitrary left/right stores and arbitrary legal host values.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-import-direct-lemma.py','guard-import-direct-chain-plan.md','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='obligations'}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
