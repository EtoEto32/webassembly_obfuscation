"""Conservative post-instantiation lifetime analysis controls and purposive sample."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
EXE=ROOT/'.tools/state-witness-census-graph-target/release/wasm-lifetime-census.exe'
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def scan(file):
    run=subprocess.run([str(EXE),str(file)],capture_output=True,text=True,encoding='utf8',timeout=45)
    assert run.returncode==0,run.stderr
    result=json.loads(run.stdout);assert result['status']=='complete',result
    return result

def controls():
    base='(type $v (func)) (memory (export "memory") 1) (data $d "A") (func (export "retire") (data.drop $d))'
    read='(func $reader (type $v) (memory.init $d (i32.const 0) (i32.const 0) (i32.const 1)))'
    cases=[
        ('private-start',True,False,read+' (start $reader) (func (export "entry"))'),
        ('exported-start',False,True,read+' (start $reader) (export "entry" (func $reader))'),
        ('direct',False,True,read+' (func (export "entry") (call $reader))'),
        ('multihop',False,True,read+' (func $bridge (call $reader)) (func (export "entry") (call $bridge))'),
        ('tail',False,True,read+' (func (export "entry") (return_call $reader))'),
        ('active-element',False,True,read+' (table 1 funcref) (elem (i32.const 0) $reader) (func (export "entry") (call_indirect (type $v) (i32.const 0)))'),
        ('passive-element',False,True,read+' (table 1 funcref) (elem $e func $reader) (func (export "entry") (table.init $e (i32.const 0) (i32.const 0) (i32.const 1)) (call_indirect (type $v) (i32.const 0)))'),
        ('declarative-dead',False,False,read+' (elem declare func $reader) (func (export "entry"))'),
        ('literal-dead',False,False,read+' (elem declare func $reader) (func $dead (drop (ref.func $reader))) (func (export "entry"))'),
        ('global-reference',False,False,read+' (global (export "g") funcref (ref.func $reader)) (func (export "entry"))'),
        ('table-expression',False,True,read+' (table 1 funcref (ref.func $reader)) (func (export "entry") (call_indirect (type $v) (i32.const 0)))'),
        ('private-unused',True,False,read+' (func (export "entry"))'),
        ('drop-only',True,False,'(func (export "entry") (data.drop $d))'),
        ('zero-length',False,True,'(func (export "entry") (memory.init $d (i32.const 0) (i32.const 1) (i32.const 0)))'),
        ('unreachable-reader',False,False,'(func (export "entry") unreachable (memory.init $d (i32.const 0) (i32.const 0) (i32.const 1)))'),
    ]
    result=[{'name':name,'safe':safe,'different':diff,'dynamic':True,'wat':'(module '+base+body+')'} for name,safe,diff,body in cases]
    # GC readers are checked statically even when a runtime disables that proposal.
    gc={
        'array-new-data':'(type $a (array (mut i8))) (data $d "A") (func (export "entry") (drop (array.new_data $a $d (i32.const 0) (i32.const 1))))',
        'array-init-data':'(type $a (array (mut i8))) (data $d "A") (func (export "entry") (array.init_data $a $d (array.new_default $a (i32.const 1)) (i32.const 0) (i32.const 0) (i32.const 1)))',
        'array-new-elem':'(type $a (array (mut funcref))) (func $f) (elem $e func $f) (func (export "entry") (drop (array.new_elem $a $e (i32.const 0) (i32.const 1))))',
        'array-init-elem':'(type $a (array (mut funcref))) (func $f) (elem $e func $f) (func (export "entry") (array.init_elem $a $e (array.new_default $a (i32.const 1)) (i32.const 0) (i32.const 0) (i32.const 1)))',
    }
    for name,body in gc.items():result.append({'name':name,'safe':False,'dynamic':False,'wat':'(module '+body+')'})
    return result

def main(source,out):
    source=source.resolve();out.mkdir(parents=True,exist_ok=False);rows=[];dynamic=[];engine=wt.Engine()
    for case in controls():
        raw=out/(case['name']+'.wasm');raw.write_bytes(wt.wat2wasm(case['wat']));(out/(case['name']+'.wat')).write_text(case['wat'])
        found=scan(raw);assert found['postInstantiation']['allLifetimeDifferencesIrrelevant']==case['safe'],case['name']
        rows.append({'name':case['name'],'expectedSufficientCondition':case['safe'],'scan':found})
        if case['dynamic']:
            outcomes=[]
            for drop in (False,True):
                with wt.Store(engine) as store:
                    ex=wt.Instance(store,wt.Module(engine,raw.read_bytes()),[]).exports(store)
                    if drop:ex['retire'](store)
                    before=hashlib.sha256(bytes(ex['memory'].read(store))).hexdigest()
                    try:ex['entry'](store);result='return'
                    except wt.Trap:result='trap'
                    outcomes.append({'outcome':result,'memory':hashlib.sha256(bytes(ex['memory'].read(store))).hexdigest(),'initialMemory':before})
            assert outcomes[0]['initialMemory']==outcomes[1]['initialMemory']
            assert (outcomes[0]!=outcomes[1])==case['different'],case['name']
            dynamic.append({'file':raw.name,'outcomes':outcomes,'different':case['different']})
    (out/'controls.json').write_text(json.dumps({'rows':rows,'dynamic':dynamic},indent=2))
    node=subprocess.run(['node',str(HERE/'post-start.mjs'),str(out.resolve())],capture_output=True,text=True,encoding='utf8',timeout=45)
    (out/'node-log.json').write_text(json.dumps({'code':node.returncode,'stdout':node.stdout,'stderr':node.stderr},indent=2));assert node.returncode==0,node.stderr
    apps=[]
    for package in json.loads((source/'provenance.json').read_text())['rows']:
        item=next(r for r in package['files'] if r['file'].endswith('.wasm'));raw=source/item['file'];assert digest(raw)==item['sha256']
        found=scan(raw);p=found['postInstantiation'];row={'package':package['package'],'sha256':item['sha256'],'source':str(raw.relative_to(ROOT)),'scan':found};apps.append(row)
        print(json.dumps({'package':package['package'],'start':found['start'],'roots':len(p['roots']),'reachableFunctions':len(p['reachableFunctions']),'reachableReaderFunctions':list(p['reachableSegmentReaders']),'allLifetimeDifferencesIrrelevant':p['allLifetimeDifferencesIrrelevant']}),flush=True)
    (out/'applications.json').write_text(json.dumps({'rows':apps,'executableSha256':digest(EXE),'controls':len(rows),'dynamicPairsPerEngine':len(dynamic)},indent=2))
    for name in ('post-start.py','post-start.mjs','post-start-plan.md','post-start-proof.md'):shutil.copy2(HERE/name,out/name)
    shutil.copy2(source/'provenance.json',out/'provenance.json')
    for name in ('src/main.rs','Cargo.toml','Cargo.lock'):shutil.copy2(HERE/'census-native'/name,out/Path(name).name)
    (out/'sha256.json').write_text(json.dumps({p.name:digest(p) for p in out.iterdir()},indent=2));print(node.stdout)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
