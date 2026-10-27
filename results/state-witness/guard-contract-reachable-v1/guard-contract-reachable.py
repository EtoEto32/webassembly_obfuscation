"""Reachable state pairs and public-only execution of uninstrumented Wasm."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sp=importlib.util.spec_from_file_location('contract',HERE/'guard-contract.py');c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];engine=wt.Engine();calls=prefixcalls=probecalls=0
    for n in (1,4,16,32):
        for repair in (False,True):
            name=f'reachable-{n:02}-'+('repair' if repair else 'expose');raw=out/(name+'.wasm');entries=' '.join(['$a']*(n-1)+['$b'])
            reset=f'(table.fill 1 (i32.const 0) (ref.func $a) (i32.const {n}))' if repair else ''
            wat=f'''(module (table (export "public") 1 1 funcref) (table {n} {n} funcref)
              (func $a (export "a") (result i32) (i32.const 101)) (func $b (export "b") (result i32) (i32.const 202))
              (elem func $a) (elem func $b) (elem (table 1) (i32.const 0) func {entries})
              (func (export "retire") (elem.drop 0) (elem.drop 1)) (func (export "release_b") (elem.drop 1))
              (func (export "mask") (table.init 1 0 (i32.const {n-1}) (i32.const 0) (i32.const 1)) (elem.drop 0) (table.init 1 1 (i32.const 0) (i32.const 0) (i32.const 1)))
              (func (export "copy") (table.copy 1 1 (i32.const 0) (i32.const 1) (i32.const {n-1})))
              (func (export "publish") {reset} (table.copy 0 1 (i32.const 0) (i32.const 0) (i32.const 1))))'''
            k.p.compile_wat(wat,raw);model=c.parse(k.p.read(raw));left,right=[False,False,False],[True,False,False]
            prepared=c.prepare(model,left,right,'public');proof=prepared['proof'];expected=[] if repair else [[['c',257],['m',2*c.g.BASE+n-1]]]
            assert proof['guard']==expected
            values={i:(256 if i<c.g.BASE*2 else 257) for i in model['cells']};values[2*c.g.BASE+n-1]=258;witness=c.extract(prepared,values)
            sequence=[x['name'] for x in witness['calls']] if witness else ['mask']+['copy']*(n-1)+['publish']
            if witness:assert len(sequence)==n+1
            compiled=wt.Module(engine,raw.read_bytes())
            assert {e.name for e in compiled.exports}=={'public','a','b','retire','release_b','mask','copy','publish'}
            with wt.Store(engine) as store:
                pair=[wt.Instance(store,compiled,[]).exports(store) for _ in range(2)];pair[0]['retire'](store);pair[1]['release_b'](store);prefixcalls+=2
                trace=[];difference=None
                for step,api in enumerate(sequence):
                    outcomes=[];observed=[]
                    for e in pair:
                        try:result=e[api](store);outcomes.append(['return',result])
                        except wt.Trap:outcomes.append(['trap'])
                        calls+=1;f=e['public'].get(store,0)
                        if isinstance(f,wt.Func):observed.append(f(store));probecalls+=1
                        else:observed.append(None)
                    trace.append({'api':api,'outcomes':outcomes,'publicFunctionResults':observed})
                    if outcomes[0]!=outcomes[1] or observed[0]!=observed[1]:
                        if difference is None:difference=step+1
                assert difference==(None if repair else n+1)
                assert trace[-1]['publicFunctionResults']==([101,101] if repair else [202,101])
            rows.append({'name':name,'source':raw.name,'repair':repair,'length':n,'proof':proof,'leftPrefix':['retire'],'rightPrefix':['release_b'],
              'sequence':sequence,'trace':trace,'firstDifference':difference,'sourceBytes':raw.stat().st_size,'instrumented':False})
    manifest={'rows':rows,'wasmtimeDiagnosticApiCalls':calls,'wasmtimePreparationApiCalls':prefixcalls,'wasmtimePublicFunctionCalls':probecalls,
      'scope':'Both states reached by original exported API prefixes. Diagnostics execute original binary and original public table function references; no helper export or hidden store patch.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    for n in ('guard-contract-reachable.py','guard-contract-reachable.mjs','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/n,out/n)
    proc=subprocess.run(['node',str(out/'guard-contract-reachable.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=60)
    (out/'node-log.json').write_text(json.dumps({'code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr},indent=2))
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));assert proc.returncode==0,proc.stderr;print(proc.stdout)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);main(p.parse_args().out)
