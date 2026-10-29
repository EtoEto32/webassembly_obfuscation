"""Controlled type-permission examples; original binaries execute unmodified."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as w
CHECK=ROOT/'.tools/gc-field-policy-target/release/gc-field-policy.exe'

TYPES='''(type $B (sub (struct (field (mut i32)) (field (mut i32)))))
 (type $T (sub $B (struct (field (mut i32)) (field (mut i32)) (field i32))))
 (type $A (sub (array (mut i32))))
 (type $DA (sub $A (array (mut i32))))'''
IMPORTS='''(import "lib" "get" (func $get (result anyref)))
 (import "lib" "array" (func $array (result anyref)))
 (import "lib" "check" (func $check (param anyref) (result i32)))'''
POLICY=[dict(type=t,deny=a,**({} if a=='create' else dict(field=f))) for t,f in ((1,1),(3,0)) for a in ('read','write','create')]

def library(secret):
    return f'''(module {TYPES}
      (global $obj (ref $T) (struct.new $T (i32.const 5) (i32.const {secret}) (i32.const 9)))
      (global $arr (ref $DA) (array.new $DA (i32.const {secret}) (i32.const 3)))
      (func (export "get") (result anyref) global.get $obj)
      (func (export "array") (result anyref) global.get $arr)
      (func (export "check") (param anyref) (result i32) local.get 0 ref.cast (ref $T) struct.get $T 1)
      (func (export "secret") (result i32) global.get $obj struct.get $T 1)
      (func (export "array-secret") (result i32) global.get $arr i32.const 0 array.get $DA))'''

def cases():
    # name, extra types, body, closure acceptance, category, optional prefix/globals
    yield 'public-read','','call $get ref.cast (ref $T) struct.get $T 0',True,'safe','',''
    yield 'pass-through','','call $get drop i32.const 1',True,'safe','',''
    yield 'secret-read','','call $get ref.cast (ref $T) struct.get $T 1',False,'read','',''
    yield 'renumbered-read','','call $get ref.cast (ref $T) struct.get $T 1',False,'read','(type (func (param i64)))',''
    yield 'duplicate-type-read','(type $copy (sub $B (struct (field (mut i32)) (field (mut i32)) (field i32))))','call $get ref.cast (ref $copy) struct.get $copy 1',False,'read','',''
    yield 'ancestor-read','','call $get ref.cast (ref $B) struct.get $B 1',False,'read','',''
    yield 'ancestor-write','','call $get ref.cast (ref $B) i32.const 77 struct.set $B 1 i32.const 1',False,'write','',''
    yield 'subtype-forge','(type $D (sub $T (struct (field (mut i32)) (field (mut i32)) (field i32) (field i64))))','i32.const 5 i32.const 77 i32.const 9 i64.const 0 struct.new $D call $check',False,'create','',''
    yield 'const-forge','','global.get $fake call $check',False,'create','','(global $fake (ref $T) (struct.new $T (i32.const 5) (i32.const 77) (i32.const 9)))'
    yield 'base-constructor','','i32.const 5 i32.const 77 struct.new $B drop i32.const 1',True,'safe','',''
    yield 'base-only-read','','i32.const 5 i32.const 77 struct.new $B struct.get $B 1',False,'conservative-reject','',''
    yield 'different-final-type','(type $Unrelated (struct (field (mut i32)) (field (mut i32)) (field i32)))','call $get ref.cast (ref $Unrelated) struct.get $Unrelated 1',True,'safe-trap','',''
    yield 'array-length','','call $array ref.cast (ref $A) array.len',True,'public-length','',''
    yield 'array-ancestor-read','','call $array ref.cast (ref $A) i32.const 0 array.get $A',False,'read','',''
    yield 'array-ancestor-fill','','call $array ref.cast (ref $A) i32.const 0 i32.const 77 i32.const 3 array.fill $A i32.const 1',False,'write','',''
    plain='(type $Plain (array (mut i32)))'
    yield 'array-copy-source',plain,'(local $dst (ref null $Plain)) i32.const 0 i32.const 3 array.new $Plain local.set $dst local.get $dst i32.const 0 call $array ref.cast (ref $A) i32.const 0 i32.const 3 array.copy $Plain $A local.get $dst i32.const 0 array.get $Plain',False,'read','',''
    yield 'array-copy-destination',plain,'call $array ref.cast (ref $A) i32.const 0 i32.const 77 i32.const 3 array.new $Plain i32.const 0 i32.const 3 array.copy $A $Plain i32.const 1',False,'write','',''
    yield 'array-subtype-forge','(type $DArray (sub $DA (array (mut i32))))','i32.const 77 i32.const 3 array.new $DArray array.len',False,'create','',''

def run(args):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True,encoding='utf8',timeout=60)
    return dict(args=[str(x) for x in args],code=p.returncode,stdout=p.stdout,stderr=p.stderr)

def python_replay(spec):
    config=w.Config();config.wasm_gc=True;config.wasm_function_references=True
    engine=w.Engine(config);rows=[]
    for case in spec['cases']:
        store=w.Store(engine);linker=w.Linker(engine)
        lib=w.Instance(store,w.Module.from_file(engine,case['library']),[])
        linker.define_instance(store,'lib',lib)
        module=w.Module.from_file(engine,case['consumer'])
        consumer=linker.instantiate(store,module)
        try: result=dict(type='return',value=consumer.exports(store)['run'](store))
        except w.Trap: result=dict(type='trap')
        rows.append(dict(name=case['name'],secret=case['secret'],result=result,
            afterStruct=lib.exports(store)['secret'](store),afterArray=lib.exports(store)['array-secret'](store)))
    return rows

def main(out):
    out.mkdir(parents=True,exist_ok=False);records=[];commands=[];spec=dict(cases=[])
    (out/'policy.json').write_text(json.dumps(POLICY,indent=2))
    for secret in (12345,54321):
        path=out/f'library-{secret}.wasm';wat=library(secret)
        (out/f'library-{secret}.wat').write_text(wat);path.write_bytes(w.wat2wasm(wat))
        for name,extra,body,accept,category,prefix,globals_ in cases():
            consumer=out/f'{name}.wasm'
            wat=f'(module {prefix} {TYPES} {extra} {IMPORTS} {globals_} (func (export "run") (result i32) {body}))'
            if not consumer.exists():
                (out/f'{name}.wat').write_text(wat);consumer.write_bytes(w.wat2wasm(wat))
            c=run([CHECK,path,out/'policy.json',consumer]);commands.append(c);assert c['code']==0,c
            check=json.loads(c['stdout'])
            closure=next(r for r in check['results'] if r['mode']=='closure')
            assert closure['accepted']==accept,(name,check)
            records.append(dict(name=name,secret=secret,expectedAcceptance=accept,category=category,check=check))
            spec['cases'].append(dict(name=name,secret=secret,category=category,library=str(path.resolve()),consumer=str(consumer.resolve())))
    (out/'replay.json').write_text(json.dumps(spec,indent=2))
    (out/'checks.json').write_text(json.dumps(records,indent=2))
    c=run(['node',HERE/'replay.mjs',out/'replay.json']);commands.append(c);assert c['code']==0,c
    node=json.loads(c['stdout']);(out/'node.json').write_text(json.dumps(node,indent=2))
    py=python_replay(spec);(out/'wasmtime.json').write_text(json.dumps(py,indent=2))
    assert node['rows']==py
    c=run(['node',HERE/'loader.mjs',CHECK,out/'replay.json',out/'policy.json']);commands.append(c);assert c['code']==0,c
    admitted=json.loads(c['stdout']);(out/'admission.json').write_text(json.dumps(admitted,indent=2))
    for r,expected,observation in zip(admitted['rows'],records,py):
        assert r['status']==('accepted' if expected['expectedAcceptance'] else 'policy-reject')
        if r['status']=='accepted':assert r['result']==observation['result']
    for r in py:
        expected={
            'public-read':5,'pass-through':1,'secret-read':r['secret'],'renumbered-read':r['secret'],
            'duplicate-type-read':r['secret'],'ancestor-read':r['secret'],'ancestor-write':1,
            'subtype-forge':77,'const-forge':77,'base-constructor':1,'base-only-read':77,
            'array-length':3,'array-ancestor-read':r['secret'],'array-ancestor-fill':1,
            'array-copy-source':r['secret'],'array-copy-destination':1,'array-subtype-forge':3}
        if r['name'] in expected:assert r['result']==dict(type='return',value=expected[r['name']])
        if r['name']=='different-final-type':assert r['result']==dict(type='trap')
        elif r['name'] in ('secret-read','renumbered-read','duplicate-type-read','ancestor-read','array-ancestor-read','array-copy-source'):
            assert r['result']==dict(type='return',value=r['secret'])
        if r['name']=='ancestor-write':assert r['afterStruct']==77
        else:assert r['afterStruct']==r['secret']
        if r['name'] in ('array-ancestor-fill','array-copy-destination'):assert r['afterArray']==77
        else:assert r['afterArray']==r['secret']
    modes={}
    for mode in ('none','local-index','canonical-exact','closure','deny-all-gc'):
        modes[mode]=dict(accepted=sum(next(x for x in r['check']['results'] if x['mode']==mode)['accepted'] for r in records),
            forbiddenAccepted=sum(r['category'] in ('read','write','create') and next(x for x in r['check']['results'] if x['mode']==mode)['accepted'] for r in records),
            safeRejected=sum(r['category'] in ('safe','safe-trap','public-length','conservative-reject') and not next(x for x in r['check']['results'] if x['mode']==mode)['accepted'] for r in records))
    summary=dict(consumerModules=len(list(cases())),libraryVariants=2,engineRunsEach=len(py),crossEngineExactRows=True,modes=modes,
        admittedExecutions=admitted['accepted'],rejectedBeforeConsumerInstantiation=admitted['rejected'],
        note='Controlled policy tests, not discovered vulnerabilities or an all-input proof.')
    (out/'commands.json').write_text(json.dumps(commands,indent=2));(out/'summary.json').write_text(json.dumps(summary,indent=2))
    sources=out/'sources';sources.mkdir()
    for p in (HERE/'experiment.py',HERE/'replay.mjs',HERE/'loader.mjs',HERE/'plan.md',HERE/'checker/src/main.rs',HERE/'checker/Cargo.toml',HERE/'checker/Cargo.lock'):
        shutil.copyfile(p,sources/p.name)
    hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
    (out/'hashes.json').write_text(json.dumps(hashes,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
