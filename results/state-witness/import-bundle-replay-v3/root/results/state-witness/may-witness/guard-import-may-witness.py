"""Replay synthesized optional-write traces on the two-import controls."""
import argparse,hashlib,importlib.util,itertools,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
q=load('mask_witness','guard-import-check.py');i=q.i;finite=load('mask_bfs','guard-import-finite.py');generic=load('mask_generic','guard-import-cached.py')
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def replay(engine,compiled,kind,values,word):
    results=[]
    for side in range(2):
        with wt.Store(engine) as store:
            ex={};refs={};trace=[];current={};block=0
            def reference(value):
                if value not in refs:refs[value]=wt.Func(store,wt.FuncType([],[wt.ValType.i32()]),lambda value=value:value)
                return refs[value]
            def snapshot():
                if kind=='memory':return list(ex['resource'].read(store,0,2))
                result=[]
                for cell in range(2):
                    f=ex['resource'].get(store,cell)
                    if not isinstance(f,wt.Func):result.append(256)
                    else:
                        v=f(store);result.append({101:259,202:260}.get(v,v))
                return result
            def touch():
                nonlocal block
                trace.append({'name':'touch'})
                for cell,value in current.get(block,{}).items():
                    if kind=='memory':ex['resource'].write(store,bytes([value]),cell)
                    else:ex['resource'].set(store,cell%i.g.BASE,reference(value))
                block+=1
            def observe():
                nonlocal block
                trace.append({'name':'observe','read':snapshot()});block+=1
            ex=wt.Instance(store,compiled,[wt.Func(store,wt.FuncType([],[]),touch),wt.Func(store,wt.FuncType([],[]),observe)]).exports(store)
            if kind=='table':refs={256:None,259:ex['resource'].get(store,0),260:ex['resource'].get(store,1)}
            ex['retire' if side==0 else 'release_b'](store)
            for cell,value in values.items():
                if kind=='memory':ex['resource'].write(store,bytes([value]),cell)
                else:ex['resource'].set(store,cell%i.g.BASE,reference(value))
            output=[]
            for call in word:
                current={r['block']:dict(r['cells']) for r in call['writes']};block=0;trace=[]
                try:ex[call['name']](store);outcome='return'
                except wt.Trap:outcome='trap'
                output.append({'outcome':outcome,'trace':trace})
            results.append(output)
    return results

def main(source,out,extractor='smt'):
    out.mkdir(parents=True,exist_ok=False);rows=[];engine=wt.Engine();comparisons=[];calls=0
    extract=q.witness if extractor=='smt' else load('direct_inputs','guard-import-direct.py').witness
    for kind in ('memory','table'):
        raw=source/(kind+'.wasm');shutil.copy2(raw,out/raw.name);module=i.k.p.read(raw);compiled=wt.Module(engine,raw.read_bytes())
        summaries={('env','touch'):{'reads':'none','writes':'may-public'},('env','observe'):{'reads':'public','writes':'none'}}
        model=i.parse(module,summaries);p=i.prepare(model,[False]*3,[True,False,False],'returns','reenter');alphabet=finite.domains(model)
        general=generic.solve(model,[False]*3,[True,False,False],'returns','reenter');solver=q.z.Solver();solver.add(general['domain'],general['formula']!=q.a.a.predicate(p['proof']['guard'],general['left'],general['left']));assert solver.check()==q.z.unsat
        comparisons.append({'kind':kind,'generalFormula':general['summary']['smt'],'status':'same-condition','proof':p['proof']})
        for assignment in itertools.product(*(alphabet[c] for c in model['cells'])):
            values=dict(zip(model['cells'],assignment));witness=extract(p,values);bfs=finite.bfs(model,((False,)*3,(True,False,False)),values,'returns','reenter',alphabet)
            assert not bfs['equal'] and witness is not None
            result=replay(engine,compiled,kind,values,witness['calls']);assert result[0]!=result[1]
            rows.append({'kind':kind,'source':raw.name,'values':sorted(values.items()),'witness':witness,'bfs':bfs,'results':result});calls+=2*len(witness['calls'])
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'comparisons':comparisons,'extractor':extractor,'pairsPerEngine':len(rows),'apiCallsPerEngine':calls,'preparationCallsPerEngine':2*len(rows)},indent=2))
    node=subprocess.run(['node',str(HERE/'guard-import-may-witness.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=45)
    (out/'node-log.json').write_text(json.dumps({'code':node.returncode,'stdout':node.stdout,'stderr':node.stderr},indent=2));assert node.returncode==0,node.stderr
    for name in ('guard-import-may-witness.py','guard-import-may-witness.mjs','guard-import-direct.py','guard-import-direct-plan.md','guard-import-finite.py','guard-import-cached.py','guard-import-generic.py','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(node.stdout)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);a.add_argument('--extractor',choices=['smt','direct'],default='smt');v=a.parse_args();main(v.source,v.out,v.extractor)
