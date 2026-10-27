"""Profile refusal checks and executable normalization boundary controls."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('import_guard',HERE/'guard-import.py');i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt


def main(out):
    out.mkdir(parents=True,exist_ok=False);summary={('env','touch'):{'reads':'none','writes':'none'}};rows=[]
    prefix='(import "env" "touch" (func $touch))'
    tests={
        'missing-summary':f'(module {prefix} (func (export "entry") (call $touch)))',
        'nonvoid-import':'(module (import "env" "touch" (func $touch (result i32))) (func (export "entry") (drop (call $touch))))',
        'argument-import':'(module (import "env" "touch" (func $touch (param i32))) (func (export "entry") (call $touch (i32.const 0))))',
        'export-import':f'(module {prefix} (export "entry" (func $touch)))',
        'import-memory':'(module (import "env" "memory" (memory 1)) (func (export "entry")))',
        'value-branch':f'(module {prefix} (memory 1) (func (export "entry") (if (i32.load8_u (i32.const 0)) (then (call $touch)))))',
        'real-loop':f'(module {prefix} (func (export "entry") (loop (call $touch) (br 0))))',
        'defined-call':f'(module {prefix} (func $internal (call $touch)) (func (export "entry") (call $internal)))',
        'global-state':f'(module {prefix} (global (mut i32) (i32.const 0)) (func (export "entry") (call $touch)))',
        'offset-store':f'(module {prefix} (memory 1) (func (export "entry") (i32.store8 offset=1 (i32.const 0) (i32.const 1))))',
        'start-function':f'(module {prefix} (func $start (call $touch)) (start $start) (func (export "entry")))',
    }
    for name,wat in tests.items():
        raw=out/(name+'.wasm');i.k.p.compile_wat(wat,raw)
        try:i.parse(i.k.p.read(raw),{} if name=='missing-summary' else summary)
        except ValueError as err:rows.append({'name':name,'status':'expected-refusal','reason':str(err)})
        else:raise AssertionError('unsound profile acceptance: '+name)
    engine=wt.Engine();normalizations=[]
    for address,value in ((0,-1),(65535,256),(65536,65),(4294967295,1)):
        raw=out/(str(address)+'-store.wasm');lowered=out/(str(address)+'-fill.wasm')
        wat=f'(module {prefix} (memory (export "memory") 1 1) (func (export "entry") (loop (br_if 0 (i32.const 0)) (call $touch) (i32.store8 (i32.const {address}) (i32.const {value})))))'
        i.k.p.compile_wat(wat,raw);module=i.k.p.read(raw);model=i.parse(module,summary);assert model['actions']
        f=i.k.p.section(module,'func')[0];f[:]=['func']+[n for n in f[1:] if n[0] in i.k.p.DECL]+i.flatten([n for n in f[1:] if n[0] not in i.k.p.DECL])
        i.k.p.compile_wat(i.k.p.w.emit(module),lowered);outputs=[]
        for src in (raw,lowered):
            with wt.Store(engine) as store:
                calls=[];touch=wt.Func(store,wt.FuncType([],[]),lambda:calls.append('touch'));ex=wt.Instance(store,wt.Module(engine,src.read_bytes()),[touch]).exports(store)
                try:ex['entry'](store);outcome='return'
                except wt.Trap:outcome='trap'
                outputs.append({'outcome':outcome,'calls':calls,'memory':hashlib.sha256(bytes(ex['memory'].read(store))).hexdigest()})
        assert outputs[0]==outputs[1];normalizations.append({'original':raw.name,'lowered':lowered.name,'expected':outputs[0]})
    (out/'manifest.json').write_text(json.dumps({'refusals':rows,'normalizations':normalizations},indent=2))
    run=subprocess.run(['node',str(HERE/'guard-import-boundary.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=30)
    (out/'node-log.json').write_text(json.dumps({'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2));assert run.returncode==0,run.stderr
    for name in ('guard-import-boundary.py','guard-import-boundary.mjs','guard-import.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(run.stdout)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
