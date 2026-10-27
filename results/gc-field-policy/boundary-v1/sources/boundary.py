"""Probe rec-group identity, packed operations, feature and policy boundaries."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from experiment import ROOT,HERE,CHECK,w,run

def pairs():
    for changed in (False,True):
        owner='(rec (type $T (struct (field (mut i32)) (field (ref null $T)))) (type $S (func)))'
        consumer='(type (func (param i64))) (rec (type $T (struct (field (mut i32)) (field (ref null $T)))) (type $S (func '+('(param i64)' if changed else '')+')))'
        lib=f'''(module {owner}
          (func (export "get") (result anyref) i32.const 12345 ref.null $T struct.new $T))'''
        client=f'''(module {consumer} (import "lib" "get" (func $get (result anyref)))
          (func (export "run") (result i32) call $get ref.cast (ref $T) struct.get $T 0))'''
        yield 'rec-sibling-'+str(int(changed)),lib,client,[dict(type=0,deny='read',field=0)],changed,({'type':'trap'} if changed else {'type':'return','value':12345})
    at='(type $A (array (mut i8)))'
    lib=f'''(module {at} (global $a (ref $A) (array.new $A (i32.const 255) (i32.const 3)))
      (func (export "get") (result anyref) global.get $a))'''
    operations={
        'packed-s':('call $get ref.cast (ref $A) i32.const 0 array.get_s $A','read',-1,''),
        'packed-u':('call $get ref.cast (ref $A) i32.const 0 array.get_u $A','read',255,''),
        'new-default':('i32.const 3 array.new_default $A array.len','create',3,''),
        'new-data':('i32.const 0 i32.const 3 array.new_data $A $d array.len','create',3,'(data $d "abc")'),
        'init-data':('call $get ref.cast (ref $A) i32.const 0 i32.const 0 i32.const 3 array.init_data $A $d i32.const 1','write',1,'(data $d "abc")'),
    }
    for name,(body,action,value,data) in operations.items():
        client=f'''(module {at} (import "lib" "get" (func $get (result anyref))) {data}
          (func (export "run") (result i32) {body}))'''
        policy=[dict(type=0,deny=action,**({} if action=='create' else dict(field=0)))]
        yield name,lib,client,policy,False,dict(type='return',value=value)
    # The consumer never obtains the owner's array. Identical shape nevertheless
    # has the same canonical type and is conservatively rejected by type policy.
    client=f'''(module {at} (func (export "run") (result i32)
      i32.const 77 i32.const 3 array.new $A i32.const 0 array.get_u $A))'''
    yield 'same-shape-independent-array',lib,client,[dict(type=0,deny='read',field=0),dict(type=0,deny='create')],False,dict(type='return',value=77)
    yield 'empty-policy',lib,client,[],True,dict(type='return',value=77)

def main(out):
    out.mkdir(parents=True,exist_ok=False);records=[];spec=[];commands=[]
    config=w.Config();config.wasm_gc=True;config.wasm_function_references=True
    engine=w.Engine(config)
    for name,lib,client,policy,expected,result in pairs():
        library=out/(name+'-lib.wasm');consumer=out/(name+'-client.wasm');pol=out/(name+'.json')
        (out/(name+'-lib.wat')).write_text(lib);(out/(name+'-client.wat')).write_text(client)
        library.write_bytes(w.wat2wasm(lib));consumer.write_bytes(w.wat2wasm(client));pol.write_text(json.dumps(policy))
        c=run([CHECK,library,pol,consumer]);commands.append(c);assert c['code']==0,c
        check=json.loads(c['stdout']);closure=next(x for x in check['results'] if x['mode']=='closure')
        assert closure['accepted']==expected,(name,check)
        if name=='empty-policy':assert not next(x for x in check['results'] if x['mode']=='deny-all-gc')['accepted']
        store=w.Store(engine);linker=w.Linker(engine);owner=w.Instance(store,w.Module.from_file(engine,str(library)),[])
        linker.define_instance(store,'lib',owner)
        i=linker.instantiate(store,w.Module.from_file(engine,str(consumer)))
        try:actual=dict(type='return',value=i.exports(store)['run'](store))
        except w.Trap:actual=dict(type='trap')
        assert actual==result,(name,actual,result)
        records.append(dict(name=name,check=check,wasmtime=actual,expectedAcceptance=expected))
        spec.append(dict(name=name,library=str(library.resolve()),consumer=str(consumer.resolve()),expected=result))
    # Explicitly unsupported and malformed are validation/configuration errors,
    # not policy rejections and not evidence of protection from unsafe code.
    unsupported={
        'threads':'(module (memory 1 1 shared))',
        'memory64':'(module (memory i64 1))',
        'multi-memory':'(module (memory 1) (memory 1))',
        'exceptions':'(module (tag (param i32)))'}
    for name,wat in unsupported.items():
        p=out/(name+'.wasm');p.write_bytes(w.wat2wasm(wat))
        c=run([CHECK,library,pol,p]);commands.append(c);assert c['code']==2,(name,c)
        records.append(dict(name=name,status='unsupported',error=c['stderr']))
    for name,policy in [('bad-type',[dict(type=999,deny='create')]),('bad-field',[dict(type=0,deny='read',field=99)]),('bad-action',[dict(type=0,deny='execute')])]:
        p=out/(name+'.json');p.write_text(json.dumps(policy));c=run([CHECK,library,p,consumer]);commands.append(c);assert c['code']==2,(name,c)
        records.append(dict(name=name,status='invalid-policy',error=c['stderr']))
    (out/'replay.json').write_text(json.dumps(spec,indent=2))
    c=run(['node',HERE/'boundary.mjs',out/'replay.json']);commands.append(c);assert c['code']==0,c
    node=json.loads(c['stdout']);assert all(r['actual']==r['expected'] for r in node['rows'])
    (out/'node.json').write_text(json.dumps(node,indent=2));(out/'records.json').write_text(json.dumps(records,indent=2));(out/'commands.json').write_text(json.dumps(commands,indent=2))
    summary=dict(executionPairs=len(spec),unsupported=len(unsupported),invalidPolicies=3,mismatches=0)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    sources=out/'sources';sources.mkdir()
    for p in (HERE/'boundary.py',HERE/'boundary.mjs',HERE/'experiment.py',HERE/'checker/src/main.rs',HERE/'checker/Cargo.lock',HERE/'soundness-obligations.md'):shutil.copyfile(p,sources/p.name)
    (out/'hashes.json').write_text(json.dumps({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
