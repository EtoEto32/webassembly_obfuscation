"""Repeat the external checkpoint experiment with independent Wasmtime execution."""
import argparse,hashlib,importlib.metadata,json,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();manifest=json.loads((source/'manifest.json').read_text());rows=[]
    def run(store,fn):
        try:return {'value':fn(store)}
        except wt.Trap:return {'trap':True}
    def host(module,stop,saved=None):
        store=wt.Store(engine);state={'polls':0,'restores':0,'stopRequested':False}
        def should():
            yes=state['polls']==stop;state['polls']+=1;state['stopRequested']|=yes;return int(yes)
        def restore(caller):
            state['restores']+=1
            if saved:
                for name,data in saved.items():
                    mem=caller.get(name);assert mem.data_len(caller)>=len(data);mem.write(caller,data,0)
        imports=[wt.Func(store,wt.FuncType([], [wt.ValType.i32()]),should),wt.Func(store,wt.FuncType([],[]),restore,access_caller=True)]
        exports=wt.Instance(store,module,imports).exports(store)
        return store,exports,state
    for r in manifest['rows']:
        if r['status']!='valid':rows.append({'name':r['name'],'kind':r['kind'],'status':r['status']});continue
        original=wt.Module(engine,(source/r['source']).read_bytes());modified=wt.Module(engine,(source/r['output']).read_bytes())
        with wt.Store(engine) as store:
            e=wt.Instance(store,original,[]).exports(store);expected=run(store,e['_start']);value=e['value'](store)
        s,e,stats=host(modified,-1);continuous=run(s,e['_start']);cv=e['value'](s);s.close()
        scenarios=[]
        for stop in (0,1,2):
            a,ae,ast=host(modified,stop);first=run(a,ae['_start'])
            if not ast['stopRequested']:
                scenarios.append({'stopAt':stop,'status':'requested-checkpoint-not-reached','firstOutcome':first,'firstStats':ast});a.close();continue
            saved={n:bytes(ae[n].read(a)) for n in ('memory','checkpoint_memory')}
            b,be,bst=host(modified,-1,saved);second=run(b,be['_start']);bv=be['value'](b)
            probe={'source':run(a,ae['__sw_data_0']),'resumed':run(b,be['__sw_data_0'])} if r['kind']=='observed' else None
            scenarios.append({'stopAt':stop,'status':'checkpoint-restored','firstOutcome':first,'firstStats':ast,
               'sourceValue':ae['value'](a),'secondOutcome':second,'secondStats':bst,'resumedValue':bv,'probe':probe,
               'matches':expected==second and value==bv});a.close();b.close()
        rows.append({'name':r['name'],'kind':r['kind'],'status':'executed','expected':expected,'expectedValue':value,
                     'continuous':continuous,'continuousValue':cv,'continuousStats':stats,'scenarios':scenarios})
    node=json.loads((source/'results.json').read_text());assert rows==node['rows']
    result={'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'matchesNode':True,
       'inputHash':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest()}
    shutil.copy2(__file__,out/'external-cross.py');(out/'results.json').write_text(json.dumps(result,indent=2))
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    print(json.dumps({'rows':len(rows),'matchesNode':True}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
