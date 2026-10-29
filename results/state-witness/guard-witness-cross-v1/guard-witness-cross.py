"""Replay generated negative witnesses in Wasmtime with scoped table tags."""
import argparse,hashlib,importlib.metadata,json,shutil,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt
BASE=1<<32
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((source/'manifest.json').read_text());node=json.loads((source/'results.json').read_text());engine=wt.Engine();rows=[];calls=tagcalls=negatives=positives=0
    def snapshot(store,e,row):
        nonlocal tagcalls
        state={}
        for rid,info in row['proof']['resources'].items():
            x=e['__guard_resource_'+rid]
            if info['kind']=='memory':state[rid]=bytes(x.read(store))
            else:
                vals=[]
                for i in range(x.size(store)):
                    f=x.get(store,i)
                    if isinstance(f,wt.Func):tagcalls+=1;tag=f(store);assert tag in (101,202);vals.append({101:257,202:258}[tag])
                    else:vals.append(256)
                state[rid]=vals
        return state
    for row,expected in zip(manifest['rows'],node['rows']):
        has_table=any(r['kind']=='table' for r in row['proof']['resources'].values())
        if has_table:
            funcs=k.p.section(k.p.read(source/row['source']),'func')
            for i,value in enumerate((101,202)):assert [x for x in funcs[i][1:] if x[0] not in k.p.DECL]==[['i32.const',str(value)]]
        compiled=wt.Module(engine,(source/row['prepared']).read_bytes());results=[]
        for sample in row['samples']:
            if sample['witness'] is None:positives+=1;results.append(None);continue
            negatives+=1;word=sample['witness']['word'];difference=None
            with wt.Store(engine) as store:
                pair=[]
                for flags in (row['left'],row['right']):
                    e=wt.Instance(store,compiled,[]).exports(store)
                    for c,value in sample['patches']:
                        rid,index=divmod(c,BASE);x=e['__guard_resource_'+str(rid)]
                        if row['proof']['resources'][str(rid)]['kind']=='memory':x.write(store,bytes([value]),index)
                        else:assert value in (256,257,258);x.set(store,index,None if value==256 else e['__guard_func_'+str(value-257)])
                    for i,live in enumerate(flags):
                        if not live:e['__guard_drop_'+str(i)](store)
                    pair.append(e)
                for step,api in enumerate(word):
                    outcomes=[]
                    for e in pair:
                        try:e[api](store);outcomes.append('return')
                        except wt.Trap:outcomes.append('trap')
                        calls+=1
                    if outcomes[0]!=outcomes[1] or snapshot(store,pair[0],row)!=snapshot(store,pair[1],row):difference=step+1;break
            assert difference==len(word);results.append({'word':word,'firstDifference':difference})
        result={'name':row['name'],'results':results};assert result==expected;rows.append(result)
    assert calls==node['apiCalls']
    result={'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'apiCalls':calls,'tagCalls':tagcalls,
      'positiveClassificationsNotReplayed':positives,'replayedNegativeWitnesses':negatives,
      'scope':'Table replay restricted to these verified pure-constant-reference fixtures; not general reference identity.'}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if isinstance(v,(str,int))}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.out)
