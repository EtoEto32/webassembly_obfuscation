"""Two-cell mask controls, independent runtimes, and endpoint-closure obligations."""
import argparse,hashlib,importlib.util,itertools,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('mask_check',HERE/'guard-import-check.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q);i=q.i;z=q.z
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def program(kind):
    imports='(import "env" "touch" (func $touch)) (import "env" "observe" (func $observe))'
    if kind=='memory':
        decl='(memory (export "resource") 1) (data "AA") (data "B") (data (i32.const 0) "AB")';op='memory.init';drop='data.drop'
    else:
        decl='(table (export "resource") 2 funcref) (func $a (export "a") (result i32) (i32.const 101)) (func $b (export "b") (result i32) (i32.const 202)) (elem func $a $a) (elem func $b) (elem (i32.const 0) func $a $b)';op='table.init';drop='elem.drop'
        # Numeric tags are host test helpers; exclude their exports from the analysis copy.
    fail=f'({op} 1 (i32.const 0) (i32.const 2) (i32.const 1))'
    return f'(module {imports} {decl} (func (export "retire") ({drop} 0) ({drop} 1)) (func (export "release_b") ({drop} 1)) (func (export "arm") ({op} 0 (i32.const 0) (i32.const 0) (i32.const 2)) {fail}) (func (export "finish") (call $touch) (call $observe) {fail}))'

def lemma():
    left=z.Array('lemma_l',z.IntSort(),z.IntSort());right=z.Array('lemma_r',z.IntSort(),z.IntSort());wl=left;wr=right;variables=[];domain=[]
    for cell in range(2):
        mask=z.Bool('choose_'+str(cell));v=z.Int('value_'+str(cell));variables.extend((mask,v));domain.append(z.And(v>=0,v<=255))
        wl=z.Store(wl,cell,z.If(mask,v,z.Select(wl,cell)));wr=z.Store(wr,cell,z.If(mask,v,z.Select(wr,cell)))
    terms=[(side,n) for side in ('l','r') for n in range(3)]+[('c',0),('c',1)];rows=[]
    typed=[z.And(z.Select(a,c)>=0,z.Select(a,c)<=255) for a in (left,right) for c in range(3)]
    for a,b in itertools.combinations_with_replacement(terms,2):
        guard=i.eq.canonical([(a,b)]);shortcut=i.eq.combine(guard,i.e.close(guard,{0,1}))
        exact=z.ForAll(variables,z.Implies(z.And(*domain),q.a.a.predicate(guard,wl,wr)))
        solver=z.Solver();solver.set(timeout=5000);solver.add(*typed,q.a.a.predicate(shortcut,left,right)!=exact);answer=solver.check();assert answer==z.unsat
        rows.append({'atom':[a,b],'answer':str(answer)})
    # Generic Boolean relations do not obey the shortcut: both cells differ,
    # neither differs after all writes, but exactly one differs after one write.
    values={'left':[0,0],'right':[1,1]}
    def relation(a,b):return (a[0]==b[0])==(a[1]==b[1])
    counter={'initial':values,'identity':relation(values['left'],values['right']),'allWrite':relation([7,9],[7,9]),'partialWrite':relation([7,0],[7,1])}
    assert counter['identity'] and counter['allWrite'] and not counter['partialWrite']
    return {'atomicObligations':rows,'generalBooleanCounterexample':counter}

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];conditions=[];engine=wt.Engine()
    for kind in ('memory','table'):
        raw=out/(kind+'.wasm');i.k.p.compile_wat(program(kind),raw);compiled=wt.Module(engine,raw.read_bytes());ast=i.k.p.read(raw)
        ast[:]=[ast[0]]+[n for n in ast[1:] if not(n[0]=='export' and json.loads(n[1]) in ('a','b'))]
        for writes in ('public','may-public'):
            summaries={('env','touch'):{'reads':'none','writes':writes},('env','observe'):{'reads':'public','writes':'none'}}
            model=i.parse(ast,summaries);p=i.prepare(model,[False]*3,[True,False,False],'returns','reenter');checks=q.check(model,p)
            assert all(c['answer']=='unsat' for c in checks)
            conditions.append({'kind':kind,'writes':writes,'proof':p['proof'],'checks':checks})
        for initial,mask,value in itertools.product(itertools.product((0,1),repeat=2),range(4),range(3)):
            results=[]
            for side in range(2):
                with wt.Store(engine) as store:
                    ex={};trace=[];refs=[]
                    def snap():
                        if kind=='memory':return list(ex['resource'].read(store,0,2))
                        return [256 if not isinstance(f:=ex['resource'].get(store,n),wt.Func) else {101:259,202:260}[f(store)] for n in range(2)]
                    def touch():
                        trace.append({'name':'touch'})
                        for cell in range(2):
                            if not mask&(1<<cell):continue
                            if kind=='memory':ex['resource'].write(store,bytes([[65,66,0][value]]),cell)
                            else:ex['resource'].set(store,cell,refs[value])
                    def observe():trace.append({'name':'observe','read':snap()})
                    ex=wt.Instance(store,compiled,[wt.Func(store,wt.FuncType([],[]),touch),wt.Func(store,wt.FuncType([],[]),observe)]).exports(store)
                    if kind=='table':refs=[ex['a'],ex['b'],None]
                    ex['retire' if side==0 else 'release_b'](store)
                    for cell,bit in enumerate(initial):
                        if kind=='memory':ex['resource'].write(store,bytes([[65,66][bit]]),cell)
                        else:ex['resource'].set(store,cell,refs[bit])
                    output=[]
                    for name in ('arm','finish'):
                        trace=[]
                        try:ex[name](store);outcome='return'
                        except wt.Trap:outcome='trap'
                        output.append({'outcome':outcome,'trace':trace})
                    results.append(output)
            expected=all(bit==0 or mask&(1<<cell) for cell,bit in enumerate(initial))
            assert (results[0]==results[1])==expected
            rows.append({'kind':kind,'source':raw.name,'initial':initial,'mask':mask,'value':value,'equal':expected,'results':results})
    result={'rows':rows,'conditions':conditions,'lemma':lemma(),'pairsPerEngine':len(rows),'entryCallsPerEngine':4*len(rows),'preparationCallsPerEngine':2*len(rows)}
    (out/'manifest.json').write_text(json.dumps(result,indent=2))
    node=subprocess.run(['node',str(HERE/'guard-import-may-pair.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=45)
    (out/'node-log.json').write_text(json.dumps({'code':node.returncode,'stdout':node.stdout,'stderr':node.stderr},indent=2));assert node.returncode==0,node.stderr
    for name in ('guard-import-may-pair.py','guard-import-may-pair.mjs','guard-import-may-plan.md','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(node.stdout)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
