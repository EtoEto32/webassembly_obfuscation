"""Adversarial controls for the conservative lifetime certificate, on two engines."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('context_analysis',HERE/'context-analysis.py');ca=importlib.util.module_from_spec(spec);spec.loader.exec_module(ca)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt
INIT='(memory.init 0 (i32.const 0) (i32.const 1) (i32.const 0))'


def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];engine=wt.Engine()
    fixtures=[
      ('drop-before-init',f'(func (export "test") (data.drop 0) {INIT})',True,False,0),
      ('init-before-drop',f'(func (export "test") {INIT} (data.drop 0))',False,True,0),
      ('callee-drop',f'(func $kill (data.drop 0)) (func (export "test") (call $kill) {INIT})',True,False,0),
      ('callee-read',f'(func $read {INIT}) (func (export "test") (call $read) (data.drop 0))',False,True,0),
      ('both-branches-drop',f'(func (export "test") (param i32) (if (local.get 0) (then (data.drop 0)) (else (data.drop 0))) {INIT})',True,False,1),
      ('one-branch-drop',f'(func (export "test") (param i32) (if (local.get 0) (then (data.drop 0))) {INIT})',False,True,1),
      ('trap-before-read',f'(func (export "test") (unreachable) {INIT})',True,False,0),
      ('branch-trap-or-drop',f'(func (export "test") (param i32) (if (local.get 0) (then (unreachable)) (else (data.drop 0))) {INIT})',True,False,1),
      ('argument-call-drop',f'(func $kill (result i32) (data.drop 0) (i32.const 0)) (func (export "test") (memory.init 0 (call $kill) (i32.const 1) (i32.const 0)))',True,False,0),
      ('unused-private-read',f'(func $unused {INIT}) (func (export "test") (data.drop 0))',True,False,0),
      ('indirect-read',f'(type $t (func)) (table 1 funcref) (elem (i32.const 0) $read) (func $read {INIT}) (func (export "test") (call_indirect (type $t) (i32.const 0)))',False,True,0),
      ('safe-zero-source', '(func (export "test") (memory.init 0 (i32.const 0) (i32.const 0) (i32.const 0)))',False,False,0),
      ('recursive-unproved','(func $again (export "test") (call $again))',False,None,0),
      ('return-unproved',f'(func (export "test") (return) {INIT})',False,False,0),
    ]
    for name,body,certified,witness,params in fixtures:
        src=out/(name+'.wasm');k.p.compile_wat('(module (memory (export "memory") 1 1) (data "x") '+body+')',src)
        module=k.p.read(src);cert=ca.certify(module,[('data',0)]);assert (cert['status']=='certified-no-segment-effect')==certified,(name,cert)
        observed,meta=k.augment(module,True);observed.append(k.p.expr('(func (export "__ctx_drop") (data.drop 0))'))
        dest=out/(name+'-observed.wasm');k.p.compile_wat(k.p.w.emit(observed),dest)
        item={'name':name,'source':src.name,'observed':dest.name,'expectedWitness':witness,'params':params,'certificate':cert,'finiteProfile':ca.finite_profile(module),'rows':[]}
        if witness is not None:
            compiled=wt.Module(engine,dest.read_bytes())
            for args in ([[]] if params==0 else [[0],[1],[-1]]):
                traces=[]
                for dropped in (False,True):
                    with wt.Store(engine) as store:
                        e=wt.Instance(store,compiled,[]).exports(store)
                        if dropped:e['__ctx_drop'](store)
                        trace=[]
                        for repeat in range(2):
                            try:result={'value':e['test'](store,*args)}
                            except wt.Trap:result={'trap':True}
                            trace.append({'result':result,'memory':hashlib.sha256(bytes(e['memory'].read(store))).hexdigest()})
                        traces.append(trace)
                item['rows'].append({'args':args,'same':traces[0]==traces[1],'traces':traces})
            assert any(not x['same'] for x in item['rows'])==witness,name
        rows.append(item)
    (out/'manifest.json').write_text(json.dumps({'cases':rows},indent=2))
    shutil.copy2(HERE/'context-controls.mjs',out/'context-controls.mjs')
    result=subprocess.run(['node',str(HERE/'context-controls.mjs'),str(out.resolve())],capture_output=True,text=True,timeout=30)
    (out/'node-log.json').write_text(json.dumps({'code':result.returncode,'stdout':result.stdout,'stderr':result.stderr},indent=2));assert result.returncode==0,result.stderr
    shutil.copy2(__file__,out/'context-controls.py');shutil.copy2(HERE/'context-analysis.py',out/'context-analysis.py')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    print(result.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
