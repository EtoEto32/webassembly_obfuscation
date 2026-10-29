"""Regression and negative checks of the restricted call-effect analyzer."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('boundary',HERE/'boundary.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


def main(source,out):
    out.mkdir(parents=True,exist_ok=False)
    pins=json.loads((source/'sha256.json').read_text())
    for name,digest in pins.items(): assert b.p.digest(source/name)==digest,name
    manifest=json.loads((source/'manifest.json').read_text())
    for e in manifest:
        file=source/e['file'];b.p.w.tool('wasm-validate',[file])
        assert b.summary(b.p.w.parse(b.p.w.tool('wasm2wat',[file,'--fold-exprs'])))==e['summary']
    prefix='(module (memory (export "memory") 1 2) '
    tests={
        'recursive':(prefix+'(func $f (export "callback") (param i32 i32 i32) (call $f (local.get 0) (local.get 1) (local.get 2))))','full'),
        'indirect':(prefix+'(type $t (func (param i32 i32 i32))) (table 1 funcref) (func (export "callback") (param i32 i32 i32) (call_indirect (type $t) (local.get 0) (local.get 1) (local.get 2) (i32.const 0))))','full'),
        'hidden-write-in-value':(prefix+'(func $f (result i32) (i32.store8 (i32.const 3) (i32.const 4)) (i32.const 8)) (func (export "callback") (param i32 i32 i32) (i32.store (call $f) (i32.const 7))))','full'),
        'local-address-mutation':(prefix+'(func (export "callback") (param i32 i32 i32) (local.set 0 (i32.const 8)) (i32.store (local.get 0) (local.get 1))))','full'),
        'helper-argument-substitution':(prefix+'(func $f (param i32 i32) (i32.store8 (local.get 1) (local.get 0))) (func (export "callback") (param i32 i32 i32) (call $f (local.get 1) (i32.add (local.get 0) (i32.const 3)))))','ranges'),
        'offset-no-wrap':(prefix+'(func (export "callback") (param i32 i32 i32) (i32.store offset=7 (local.get 0) (local.get 1))))','ranges'),
        'arithmetic-wrap':(prefix+'(func (export "callback") (param i32 i32 i32) (i32.store (i32.add (local.get 0) (i32.const 7)) (local.get 1))))','ranges'),
    }
    rows=[]
    for name,(wat,kind) in tests.items():
        f=out/(name+'.wat');f.write_text(wat,encoding='utf8');binary=f.with_suffix('.wasm')
        b.p.w.tool('wat2wasm',[f,'-o',binary]);b.p.w.tool('wasm-validate',[binary])
        actual=b.summary(b.p.w.parse(b.p.w.tool('wasm2wat',[binary,'--fold-exprs'])))
        assert actual['kind']==kind,(name,actual)
        rows.append({'name':name,'summary':actual})
    def get(name):return next(x['summary'] for x in rows if x['name']==name)
    assert get('helper-argument-substitution')['writes'][0]['addr']==['add',['arg',0],['const',3]]
    assert get('offset-no-wrap')['writes'][0]['offset']==7
    assert get('arithmetic-wrap')['writes'][0]['offset']==0
    # Direct-only effect approximation would miss this helper's write.
    transitive=next(x for x in manifest if x['file']=='transitive-raw.wasm')
    assert transitive['summary']['writes']
    raw=b.p.w.parse(b.p.w.tool('wasm2wat',[source/'transitive-raw.wasm','--fold-exprs']))
    functions=[x for x in raw[1:] if x[0]=='func']
    exports={x[1]:x[2] for x in raw[1:] if x[0]=='export'}
    imports=[x for x in raw[1:] if x[0]=='import' and x[3][0]=='func']
    callback=functions[int(exports['"callback"'][1])-len(imports)]
    assert 'store' not in b.p.w.emit(callback)
    subprocess.run(['node','--check',str(HERE/'boundary.cjs')],capture_output=True,check=True)
    report={'pinsVerified':len(pins),'wasmValidated':len(manifest),'summariesRecomputed':len(manifest),'regressions':rows,'directOnlyWouldMissHelperWrite':True}
    shutil.copy2(__file__,out/'boundary-audit.py')
    (out/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (out/'sha256.json').write_text(json.dumps({x.name:b.p.digest(x) for x in out.iterdir() if x.is_file()},indent=2),encoding='utf8')
    print(json.dumps({'pinsVerified':len(pins),'summariesRecomputed':len(manifest),'regressions':len(rows)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();main(a.source.resolve(),a.output.resolve())
