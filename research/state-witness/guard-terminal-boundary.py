"""Reject a branch/global program where one-call testing is insufficient."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('fast',HERE/'guard-terminal-fast.py');f=importlib.util.module_from_spec(sp);sp.loader.exec_module(f)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def main(out):
    out.mkdir(parents=True,exist_ok=False);source=out/'global-phase.wasm'
    wat='''(module (memory 1 1) (data "A") (global (mut i32) (i32.const 0))
      (func (export "probe") (result i32) (if (global.get 0) (then
        (memory.init 0 (i32.const 0) (i32.const 0) (i32.const 1)) (return (i32.const 42)))) (unreachable))
      (func (export "arm") (global.set 0 (i32.const 1))))'''
    k.p.compile_wat(wat,source);module=k.p.read(source)
    try:f.c.parse(module);raise AssertionError('unsupported profile accepted')
    except ValueError as e:rejection=str(e)
    module.append(k.p.expr('(func (export "__drop") (data.drop 0))'));prepared=out/'global-phase-prepared.wasm';k.p.compile_wat(k.p.w.emit(module),prepared)
    engine=wt.Engine();compiled=wt.Module(engine,prepared.read_bytes());traces=[];calls=0
    for sequence in (['arm'],['probe'],['arm','probe']):
        with wt.Store(engine) as store:
            pair=[wt.Instance(store,compiled,[]).exports(store) for _ in range(2)];pair[0]['__drop'](store);trace=[]
            for api in sequence:
                outcomes=[]
                for e in pair:
                    try:outcomes.append(['return',e[api](store)])
                    except wt.Trap:outcomes.append(['trap'])
                    calls+=1
                trace.append({'api':api,'outcomes':outcomes})
                if any(x[0]=='trap' for x in outcomes):break
            traces.append({'sequence':sequence,'trace':trace})
    assert all(x['trace'][0]['outcomes'][0]==x['trace'][0]['outcomes'][1] for x in traces[:2]);assert traces[2]['trace'][-1]['outcomes']==[['trap'],['return',42]]
    (out/'manifest.json').write_text(json.dumps({'rejectedProfile':rejection,'prepared':prepared.name,'wasmtimeApiCalls':calls,'traces':traces},indent=2))
    for n in ('guard-terminal-boundary.py','guard-terminal-boundary.mjs','guard-terminal-fast.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    result=subprocess.run(['node',str(out/'guard-terminal-boundary.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=30)
    (out/'node-log.json').write_text(json.dumps({'code':result.returncode,'stdout':result.stdout,'stderr':result.stderr},indent=2));(out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));assert result.returncode==0,result.stderr;print(result.stdout)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
