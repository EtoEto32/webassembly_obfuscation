"""Long delayed host observations for the same-output baseline comparison."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('generic_chain',HERE/'guard-import-generic.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);i=b.q.i;z=b.z
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt


def wat(n):
    return f'''(module (import "env" "touch" (func $touch))
      (table (export "public") 1 1 funcref) (table {n} {n} funcref)
      (func $a (result i32) (i32.const 101)) (func $b (result i32) (i32.const 202))
      (elem func $a) (elem func $b) (elem (i32.const 0) func $b) (elem (table 1) (i32.const 0) func {' '.join('$b' for _ in range(n))})
      (func (export "retire") (elem.drop 0) (elem.drop 1)) (func (export "release_b") (elem.drop 1))
      (func (export "seed") (table.init 1 0 (i32.const 0) (i32.const 0) (i32.const 1)) (table.init 1 1 (i32.const 0) (i32.const 2) (i32.const 1)))
      (func (export "step") (table.copy 0 1 (i32.const 0) (i32.const {n-1}) (i32.const 1)) (call $touch)
        (table.copy 1 1 (i32.const 1) (i32.const 0) (i32.const {n-1}))))'''


def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];runtime=[];engine=wt.Engine()
    for n in (1,8,32,96):
        raw=out/('chain-'+str(n)+'.wasm');i.k.p.compile_wat(wat(n),raw);module=i.k.p.read(raw);left=[False]*4;right=[True,False,False,False]
        for reads in ('none','public'):
            summaries={('env','touch'):{'reads':reads,'writes':'public'}};model=i.parse(module,summaries)
            started=time.perf_counter();p=i.prepare(model,left,right,'public','reenter');ks=time.perf_counter()-started
            expected=[] if reads=='none' else [[['c',258],['m',2*i.g.BASE]]];assert p['proof']['guard']==expected
            result=b.solve(model,left,right,'public','reenter');solver=z.Solver();solver.set(timeout=5000)
            solver.add(result['domain'],b.q.a.a.predicate(p['proof']['guard'],result['left'],result['left'])!=result['formula']);assert solver.check()==z.unsat
            rows.append({'name':'chain-'+str(n)+'-'+reads,'source':raw.name,'length':n,'left':left,'right':right,'proof':p['proof'],'specializedSeconds':ks,'generic':result['summary']})
            traces=[];host_calls=api_calls=tags=0
            for side in (0,1):
                with wt.Store(engine) as store:
                    ex={};trace=[]
                    def touch():
                        nonlocal host_calls,tags
                        host_calls+=1;ref=ex['public'].get(store,0);value=None
                        if reads=='public':value=ref(store) if isinstance(ref,wt.Func) else None;tags+=isinstance(ref,wt.Func)
                        trace.append({'name':'touch','read':value});ex['public'].set(store,0,None)
                    f=wt.Func(store,wt.FuncType([],[]),touch);ex=wt.Instance(store,wt.Module(engine,raw.read_bytes()),[f]).exports(store)
                    ex['retire' if side==0 else 'release_b'](store)
                    outputs=[]
                    for name in ['seed']+['step']*n:
                        trace=[]
                        try:ex[name](store);outcome='return'
                        except wt.Trap:outcome='trap'
                        api_calls+=1;ref=ex['public'].get(store,0);public=ref(store) if isinstance(ref,wt.Func) else None;tags+=isinstance(ref,wt.Func)
                        outputs.append({'api':name,'outcome':outcome,'hostTrace':trace,'public':public})
                    traces.append(outputs)
            difference=next((j+1 for j,(a,c) in enumerate(zip(*traces)) if a!=c),None);assert difference==(n+1 if reads=='public' else None)
            runtime.append({'name':rows[-1]['name'],'source':raw.name,'length':n,'reads':reads,'traces':traces,'difference':difference,'apiCalls':api_calls,'hostCalls':host_calls,'pureTagCalls':tags,'preparationCalls':2})
        print(json.dumps({'length':n,'latestGenericSeconds':result['summary']['seconds']}),flush=True)
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'runtime':runtime},indent=2))
    run=subprocess.run(['node',str(HERE/'guard-import-chain.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2));assert run.returncode==0,run.stderr
    for name in ('guard-import-chain.py','guard-import-chain.mjs','guard-import-generic.py','guard-import-check.py','guard-import.py','guard-environment-check.py','guard-contract-check.py','guard-table-check.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(run.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
