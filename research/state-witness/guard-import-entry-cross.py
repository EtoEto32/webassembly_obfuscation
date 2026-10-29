"""Wasmtime entry-only migration plus local host-effect trace replay."""
import argparse,hashlib,importlib.metadata,json,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def main(source,node,out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();input_data=json.loads((source/'manifest.json').read_text());expected=json.loads((node/'results.json').read_text());rows=[];calls=touch_calls=0
    def run(store,instance):
        nonlocal calls
        calls+=1
        try:return {'return':instance['entry'](store)}
        except wt.Trap:return {'trap':True}
    def host(module,stop,write,saved=None):
        store=wt.Store(engine);stats={'polls':0,'requested':False};trace=[] if saved is None else saved['trace'].copy()
        def touch(caller):
            nonlocal touch_calls
            touch_calls+=1;trace.append({'name':'touch','write':write})
            if write:caller.get('memory').write(caller,b'\0',7)
        def poll():
            yes=stats['polls']==stop;stats['polls']+=1;stats['requested']|=yes;return int(yes)
        def restore(caller):
            if saved:
                for name,data in saved['memories'].items():caller.get(name).write(caller,data)
        functions={('env','touch'):wt.Func(store,wt.FuncType([],[]),touch,access_caller=True),
            ('host','should_migrate'):wt.Func(store,wt.FuncType([], [wt.ValType.i32()]),poll),
            ('host','restore_memory'):wt.Func(store,wt.FuncType([],[]),restore,access_caller=True)}
        imports=[functions[(v.module,v.name)] for v in module.imports]
        return store,wt.Instance(store,module,imports).exports(store),stats,trace
    def observe(store,instance,trace):
        data=bytes(instance['memory'].read(store,0,65536));return {'hostTrace':trace.copy(),'memory':{'sha256':hashlib.sha256(data).hexdigest(),'bytes7to10':list(data[7:11])}}
    for source_row in input_data['rows']:
        variant=next(v for v in source_row['variants'] if v['backend']=='migrate')
        if variant['status']!='valid':rows.append({'name':source_row['name'],'status':variant['status']});continue
        compiled=wt.Module(engine,(source/variant['binary']).read_bytes());original=wt.Module(engine,(source/source_row['original']).read_bytes())
        for write in (False,True):
            nr=next(r for r in expected['rows'] if r['backend']=='migrate' and r['name']==source_row['name'] and r['write']==write)
            store,instance,_,trace=host(original,-1,write);reference={'outcome':run(store,instance),**observe(store,instance,trace)};store.close();assert reference==nr['reference']
            store,instance,stats,trace=host(compiled,-1,write);continuous={'outcome':run(store,instance),**observe(store,instance,trace)};store.close();assert continuous==nr['continuous'] and stats['polls']==nr['polls'];scenarios=[]
            for stop,ns in enumerate(nr['scenarios']):
                store,instance,stats,trace=host(compiled,stop,write);first=run(store,instance)
                if not stats['requested']:
                    result={'stop':stop,'status':'checkpoint-not-reached','firstOutcome':first};assert result==ns;scenarios.append(result);store.close();continue
                before=observe(store,instance,trace);saved={'trace':trace.copy(),'memories':{name:bytes(instance[name].read(store)) for name in ('memory','checkpoint_memory')}};store.close()
                store,instance,_,trace=host(compiled,-1,write,saved);second=run(store,instance);after=observe(store,instance,trace);store.close()
                result={'stop':stop,'status':'restored','firstOutcome':first,'before':before,'outcome':second,**after,
                    'entryMatches':second==reference['outcome'],'hostTraceMatches':after['hostTrace']==reference['hostTrace'],'memoryMatches':after['memory']==reference['memory']}
                assert result==ns;scenarios.append(result)
            rows.append({'name':source_row['name'],'write':write,'reference':reference,'continuous':continuous,'scenarios':scenarios})
    result={'rows':rows,'apiCalls':calls,'hostTouchCalls':touch_calls,'wasmtime':importlib.metadata.version('wasmtime'),
        'restored':sum(s['status']=='restored' for r in rows for s in r.get('scenarios',[])),
        'memoryDifferences':sum(s.get('memoryMatches') is False for r in rows for s in r.get('scenarios',[])),
        'hostTraceDifferences':sum(s.get('hostTraceMatches') is False for r in rows for s in r.get('scenarios',[])),
        'scope':'Original entry only, fixed migrate transformation and local host-effect trace. Outside the closed analysis profile; no Weave JS driver claim.'}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for name in ('source','node','out'):a.add_argument(name,type=Path)
    v=a.parse_args();main(v.source,v.node,v.out)
