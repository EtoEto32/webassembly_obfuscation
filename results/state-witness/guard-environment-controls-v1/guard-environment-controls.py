"""Original-export, reachable-state controls for host-write contracts."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('environment',HERE/'guard-environment.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e);k=e.k
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for kind in ('memory','table'):
        for mode in ('public','private','repair'):
            name=kind+'-'+mode;public=mode!='private';export='(export "resource")' if public else ''
            if kind=='memory':
                declarations=f'(memory {export} 1 1) (data "A") (data "B") (data (i32.const 0) "A")'
                pre='(memory.fill (i32.const 0) (i32.const 65) (i32.const 1))' if mode=='repair' else ''
                body=pre+' (memory.init 0 (i32.const 0) (i32.const 0) (i32.const 1)) (data.drop 0) (memory.init 1 (i32.const 0) (i32.const 0) (i32.const 1))'
                drop='data.drop';reader='(func (export "read") (param i32) (result i32) (i32.load8_u (local.get 0)))'
            else:
                declarations=f'(table {export} 1 1 funcref) (func $a (export "a") (result i32) (i32.const 101)) (func $b (export "b") (result i32) (i32.const 202)) (elem func $a) (elem func $b) (elem (i32.const 0) func $a)'
                pre='(table.fill (i32.const 0) (ref.func $a) (i32.const 1))' if mode=='repair' else ''
                body=pre+' (table.init 0 (i32.const 0) (i32.const 0) (i32.const 1)) (elem.drop 0) (table.init 1 (i32.const 0) (i32.const 0) (i32.const 1))'
                drop='elem.drop';reader=''
            wat=f'(module {declarations} (func (export "retire") ({drop} 0) ({drop} 1)) (func (export "release_b") ({drop} 1)) (func (export "mask") {body}) {reader})'
            raw=out/(name+'.wasm');k.p.compile_wat(wat,raw);model=e.c.parse(k.p.read(raw));values={i:65 if i<e.c.g.BASE else 257 for i in model['cells']}
            for contract in ('full','public','returns'):
                for protocol in ('reenter','terminal'):
                    prepared=e.prepare(model,[False]*3,[True,False,False],contract,protocol);witness=e.extract(prepared,values)
                    legacy=e.p.prepare(model,[False]*3,[True,False,False],contract,protocol)['proof']
                    closed=e.prepare(model,[False]*3,[True,False,False],contract,protocol,False)['proof']
                    assert closed['guard']==legacy['guard']
                    words=[witness['steps']] if witness else [[{'kind':'call','name':a['name'],'args':[0] if a['observation']=='read-byte' else []}] for a in model['actions']]
                    if not witness:
                        writes=next(e.assignments(prepared,values,values))
                        words.append([{'kind':'write','cells':list(map(list,writes.items()))},{'kind':'call','name':'mask','args':[]}])
                    rows.append({'name':name+'-'+contract+'-'+protocol,'source':raw.name,'kind':kind,'mode':mode,
                        'proof':prepared['proof'],'legacyGuard':legacy['guard'],'witness':witness,'words':words,
                        'execution':'not-observable-through-original-exports' if mode=='private' and contract=='full' else 'run'})
    k.p.compile_wat('(module (func (export "foreign") (result i32) (i32.const 999)))',out/'foreign.wasm')
    (out/'manifest.json').write_text(json.dumps({'rows':rows,'scope':'Original exports; initial states reached via retire/release_b; no private patches or helper exports.'},indent=2))
    engine=wt.Engine();foreign_module=wt.Module(engine,(out/'foreign.wasm').read_bytes());outcomes=[];calls=prep=tags=writes=0
    for row in rows:
        if row['execution']!='run':outcomes.append({'name':row['name'],'status':row['execution']});continue
        compiled=wt.Module(engine,(out/row['source']).read_bytes());traces=[]
        for word in row['words']:
            with wt.Store(engine) as store:
                pair=[wt.Instance(store,compiled,[]).exports(store) for _ in range(2)];foreign=wt.Instance(store,foreign_module,[]).exports(store)['foreign']
                pair[0]['retire'](store);pair[1]['release_b'](store);prep+=2;trace=[];difference=None
                for index,step in enumerate(word):
                    result=[]
                    if step['kind']=='write':
                        for i,v in step['cells']:
                            for instance in pair:
                                if row['kind']=='memory':instance['resource'].write(store,bytes([v]),i)
                                else:instance['resource'].set(store,i%e.c.g.BASE,None if v==256 else foreign)
                                writes+=1
                        result=[['write'],['write']]
                    else:
                        for instance in pair:
                            try:result.append(['return',instance[step['name']](store,*step['args'])])
                            except wt.Trap:result.append(['trap'])
                            calls+=1
                    snapshots=[]
                    if row['proof']['contract']!='returns' and row['mode']!='private':
                        for instance in pair:
                            if row['kind']=='memory':snapshots.append(list(bytes(instance['resource'].read(store))))
                            else:
                                val=instance['resource'].get(store,0)
                                if val is None or isinstance(val,wt.Val) and val.value is None:snapshots.append([None])
                                else:snapshots.append([val(store)]);tags+=1
                    equal=not snapshots or snapshots[0]==snapshots[1]
                    trace.append({'kind':step['kind'],'outcomes':result,'storeEqual':equal,'first':[] if not snapshots else [a[0] for a in snapshots]})
                    if result[0]!=result[1] or not equal:difference=index+1;break
                    if row['proof']['protocol']=='terminal' and result[0][0]=='trap':break
                assert difference==(len(word) if row['witness'] else None),(row['name'],trace)
                traces.append({'difference':difference,'trace':trace})
        outcomes.append({'name':row['name'],'status':'matched','traces':traces})
    result={'rows':outcomes,'apiCalls':calls,'preparationApiCalls':prep,'pureReferenceTagCalls':tags,'cellWrites':writes}
    (out/'wasmtime.json').write_text(json.dumps(result,indent=2))
    run=subprocess.run(['node',str(HERE/'guard-environment-controls.mjs'),str(out.resolve())],text=True,encoding='utf8',capture_output=True,timeout=40)
    (out/'node-log.json').write_text(json.dumps({'code':run.returncode,'stdout':run.stdout,'stderr':run.stderr},indent=2));assert run.returncode==0,run.stderr
    for name in ('guard-environment-controls.py','guard-environment-controls.mjs','guard-environment.py','guard-environment-plan.md','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(run.stdout)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('out',type=Path);main(a.parse_args().out)
