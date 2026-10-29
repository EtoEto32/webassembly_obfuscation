"""Counterexample to checking host-write closure only at the initial condition."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('environment',HERE/'guard-environment.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];engine=wt.Engine();api_calls=prep_calls=write_calls=0
    for repair in (False,True):
        name='repair' if repair else 'interleave';raw=out/(name+'.wasm')
        copy='(table.copy 1 0 (i32.const 0) (i32.const 0) (i32.const 1))'
        wat=f'''(module (table (export "public") 1 1 funcref) (table 2 2 funcref)
          (func $a (export "a") (result i32) (i32.const 101)) (func $b (export "b") (result i32) (i32.const 202))
          (elem func $a) (elem func $b) (elem func $b)
          (elem (table 0) (i32.const 0) func $a) (elem (table 1) (i32.const 0) func $b)
          (func (export "retire_left") (elem.drop 0) (elem.drop 2))
          (func (export "retire_right") (elem.drop 2))
          (func (export "arm") {copy} (table.init 1 0 (i32.const 1) (i32.const 0) (i32.const 1)) (elem.drop 1)
            (table.init 1 2 (i32.const 1) (i32.const 0) (i32.const 1)))
          (func (export "publish") {copy if repair else ''} (table.init 1 1 (i32.const 1) (i32.const 0) (i32.const 1))
            (table.copy 0 1 (i32.const 0) (i32.const 0) (i32.const 1)) (table.init 1 2 (i32.const 1) (i32.const 0) (i32.const 1))))'''
        e.k.p.compile_wat(wat,raw);model=e.c.parse(e.k.p.read(raw));left=[False,True,False,False,False];right=[True,True,False,False,False]
        values={i:257 if i==e.c.g.BASE else 258 if i==2*e.c.g.BASE else 256 for i in model['cells']};compiled=wt.Module(engine,raw.read_bytes())
        for protocol in ('reenter','terminal'):
            baseline=e.p.prepare(model,left,right,'public',protocol)['proof'];prepared=e.prepare(model,left,right,'public',protocol);witness=e.extract(prepared,values)
            assert baseline['guard']==[],baseline
            assert prepared['proof']['guard']==(None if not repair and protocol=='reenter' else [])
            if witness:assert witness['shortestLength']==3 and witness['hostWrites']==1
            # Check the same diagnostic trace on every variant; terminal stops at arm.
            word=[{'kind':'call','name':'arm','args':[]},{'kind':'write','cells':[[e.c.g.BASE,256]]},{'kind':'call','name':'publish','args':[]}]
            with wt.Store(engine) as store:
                pair=[wt.Instance(store,compiled,[]).exports(store) for _ in range(2)];pair[0]['retire_left'](store);pair[1]['retire_right'](store);prep_calls+=2;trace=[];difference=None
                for i,step in enumerate(word):
                    outcomes=[]
                    for instance in pair:
                        if step['kind']=='write':instance['public'].set(store,0,None);outcomes.append(['write']);write_calls+=1
                        else:
                            try:outcomes.append(['return',instance[step['name']](store)])
                            except wt.Trap:outcomes.append(['trap'])
                            api_calls+=1
                    refs=[instance['public'].get(store,0) for instance in pair];public=[ref(store) if isinstance(ref,wt.Func) else None for ref in refs]
                    trace.append({'kind':step['kind'],'outcomes':outcomes,'public':public})
                    if public[0]!=public[1] or outcomes[0]!=outcomes[1]:difference=i+1;break
                    if protocol=='terminal' and outcomes[0][0]=='trap':break
                assert difference==(3 if witness else None)
            rows.append({'name':name+'-'+protocol,'source':raw.name,'left':left,'right':right,'legacyGuard':baseline['guard'],'proof':prepared['proof'],'witness':witness,'word':word,'difference':difference,'trace':trace})
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'apiCalls':api_calls,'preparationApiCalls':prep_calls,'cellWrites':write_calls},indent=2))
    run=subprocess.run(['node',str(HERE/'guard-environment-interleave.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=30)
    (out/'node-log.json').write_text(json.dumps({'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2));assert run.returncode==0,run.stderr
    for name in ('guard-environment-interleave.py','guard-environment-interleave.mjs','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(run.stdout)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
