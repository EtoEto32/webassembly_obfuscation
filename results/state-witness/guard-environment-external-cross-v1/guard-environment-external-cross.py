"""Independent runtime for the migrate public-memory host-write experiment."""
import argparse,hashlib,importlib.metadata,json,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def main(source,node,out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();manifest=json.loads((source/'manifest.json').read_text());expected=json.loads((node/'results.json').read_text());rows=[];calls=writes=0
    def run(store,instance,name):
        nonlocal calls
        calls+=1
        try:return {'return':instance[name](store)}
        except wt.Trap:return {'trap':True}
    def host(module,stop,saved=None):
        store=wt.Store(engine);stats={'polls':0,'requested':False}
        def poll():
            yes=stats['polls']==stop;stats['polls']+=1;stats['requested']|=yes;return int(yes)
        def restore(caller):
            if saved:
                for name,data in saved.items():caller.get(name).write(caller,data)
        imports=[wt.Func(store,wt.FuncType([], [wt.ValType.i32()]),poll),wt.Func(store,wt.FuncType([],[]),restore,access_caller=True)]
        return store,wt.Instance(store,module,imports).exports(store),stats
    def observe(store,instance):
        data=bytes(instance['memory'].read(store,0,65536));return {'sha256':hashlib.sha256(data).hexdigest(),'bytes7to10':list(data[7:11])}
    def diagnose(store,instance,write):
        nonlocal writes
        before=observe(store,instance)
        if write:instance['memory'].write(store,b'\0',7);writes+=1
        after_write=observe(store,instance);outcome=run(store,instance,'mask');return {'before':before,'afterWrite':after_write,'outcome':outcome,'after':observe(store,instance)}
    for row in manifest['rows']:
        variant=next(v for v in row['variants'] if v['backend']=='migrate');nr=next(r for r in expected['rows'] if r['backend']=='migrate' and r['name']==row['name'])
        if variant['status']!='valid':rows.append({'name':row['name'],'status':variant['status']});continue
        module=wt.Module(engine,(source/variant['binary']).read_bytes());continuous=[];scenarios=[]
        for write,nc in zip((False,True),nr['continuous']):
            store,instance,stats=host(module,-1);entry=run(store,instance,'retire');result={'write':write,'entry':entry,**diagnose(store,instance,write)}
            assert result==nc and stats['polls']==nr['polls'];continuous.append(result);store.close()
        for stop in range(nr['polls']+1):
            store,instance,stats=host(module,stop);first=run(store,instance,'retire')
            if not stats['requested']:
                result={'stop':stop,'status':'checkpoint-not-reached','firstOutcome':first};assert result in nr['scenarios'];scenarios.append(result);store.close();continue
            saved={name:bytes(instance[name].read(store)) for name in ('memory','checkpoint_memory')};store.close()
            for write in (False,True):
                store,instance,_=host(module,-1,saved);entry=run(store,instance,'retire');diag=diagnose(store,instance,write);store.close();base=next(c for c in continuous if c['write']==write)
                result={'stop':stop,'write':write,'status':'restored','firstOutcome':first,'entry':entry,'entryMatches':entry==base['entry'],
                    'preDiagnosticMemoryMatches':diag['before']==base['before'],'diagnosticMatches':diag['outcome']==base['outcome'] and diag['after']==base['after'],**diag}
                assert result in nr['scenarios'];scenarios.append(result)
        rows.append({'name':row['name'],'continuous':continuous,'scenarios':scenarios})
    result={'rows':rows,'apiCalls':calls,'hostCellWrites':writes,'wasmtime':importlib.metadata.version('wasmtime'),
        'restored':sum(s['status']=='restored' for r in rows for s in r.get('scenarios',[])),
        'diagnosticDifferences':sum(s.get('diagnosticMatches') is False for r in rows for s in r.get('scenarios',[])),
        'scope':'migrate experiment adapter, one diagnostic call; original guest memory prefix only. Not an author-confirmed supported use or a Weave JS lifecycle replay.'}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for name in ('source','node','out'):a.add_argument(name,type=Path)
    v=a.parse_args();main(v.source,v.node,v.out)
