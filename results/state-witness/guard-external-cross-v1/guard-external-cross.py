"""Wasmtime repetition of the experimental migrate host's public observations."""
import argparse,hashlib,importlib.metadata,json,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt

def main(source,node,out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();manifest=json.loads((source/'manifest.json').read_text());expected=json.loads((node/'results.json').read_text());rows=[];calls=tags=0
    def run(store,e,name):
        nonlocal calls
        calls+=1
        try:return {'return':e[name](store)}
        except wt.Trap:return {'trap':True}
    def host(module,stop,saved=None):
        store=wt.Store(engine);stats={'polls':0,'requested':False}
        def poll():
            yes=stats['polls']==stop;stats['polls']+=1;stats['requested']|=yes;return int(yes)
        def restore(caller):
            if saved:
                for n,data in saved.items():caller.get(n).write(caller,data)
        imports=[wt.Func(store,wt.FuncType([], [wt.ValType.i32()]),poll),wt.Func(store,wt.FuncType([],[]),restore,access_caller=True)]
        return store,wt.Instance(store,module,imports).exports(store),stats
    def diagnose(store,e,sequence):
        nonlocal tags
        trace=[]
        for name in sequence:
            result=run(store,e,name);f=e['public'].get(store,0)
            if isinstance(f,wt.Func):value=f(store);tags+=1;assert value in (101,202)
            else:value=None
            trace.append({'api':name,'result':result,'publicValue':value})
        return trace
    for r in manifest['rows']:
        v=next(v for v in r['variants'] if v['backend']=='migrate');nr=next(x for x in expected['rows'] if x['backend']=='migrate' and x['name']==r['name'])
        if v['status']!='valid':rows.append({'name':r['name'],'status':v['status']});continue
        module=wt.Module(engine,(source/v['binary']).read_bytes());s,e,stats=host(module,-1)
        entry=run(s,e,'retire');count=stats['polls'];trace=diagnose(s,e,r['sequence']);s.close()
        assert entry==nr['continuous']['entry'] and trace==nr['continuous']['trace'] and count==nr['polls'];scenarios=[]
        for stop,ns in enumerate(nr['scenarios']):
            a,ae,ast=host(module,stop);first=run(a,ae,'retire');assert first==ns['firstOutcome']
            if not ast['requested']:
                assert ns['status']=='checkpoint-not-reached';scenarios.append({'stop':stop,'status':ns['status']});a.close();continue
            saved={n:bytes(ae[n].read(a)) for n in ('memory','checkpoint_memory')};a.close()
            b,be,bst=host(module,-1,saved);second=run(b,be,'retire');observed=diagnose(b,be,r['sequence']);b.close()
            assert second==ns['restoredOutcome'] and observed==ns['trace'];scenarios.append({'stop':stop,'status':'restored','entryMatches':second==entry,'publicObservationMatches':observed==trace,'trace':observed})
        rows.append({'name':r['name'],'status':'executed','continuousMatchesNode':True,'scenarios':scenarios})
    result={'rows':rows,'wasmtime':importlib.metadata.version('wasmtime'),'apiCalls':calls,'publicFunctionCalls':tags,
       'restored':sum(s['status']=='restored' for r in rows for s in r.get('scenarios',[])),
       'publicDifferences':sum(s.get('publicObservationMatches') is False for r in rows for s in r.get('scenarios',[])),
       'scope':'Experimental migrate adapter only. Weave JavaScript lifecycle is separately tested in Node; no claim of author-supported migrate re-entry.'}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('source','node','out'):p.add_argument(n,type=Path)
    v=p.parse_args();main(v.source,v.node,v.out)
