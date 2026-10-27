"""Wasmtime replay of host-write witnesses and finite positive traces."""
import argparse,hashlib,importlib.metadata,json,shutil,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
BASE=1<<32

def main(source,node_dir,out):
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((source/'manifest.json').read_text());node=json.loads((node_dir/'results.json').read_text());engine=wt.Engine();rows=[];calls=tags=terminated=writes=0
    foreign_module=wt.Module(engine,(source/'foreign.wasm').read_bytes())
    def patch(store,instance,foreign,row,cells,external):
        nonlocal writes
        for cell,value in cells:
            if external:assert cell in row['proof']['writableCells']
            rid,index=divmod(cell,BASE);resource=instance['__guard_resource_'+str(rid)]
            if row['proof']['resources'][str(rid)]['kind']=='memory':resource.write(store,bytes([value]),index)
            else:resource.set(store,index,None if value==256 else foreign if value==row['proof']['foreignReference'] else instance['__guard_func_'+str(value-257)])
            if external:writes+=1
    def snapshot(store,instance,row):
        nonlocal tags
        result={}
        for rid in row['proof']['observedResources']:
            resource=instance['__guard_resource_'+str(rid)]
            if row['proof']['resources'][str(rid)]['kind']=='memory':result[rid]=bytes(resource.read(store));continue
            values=[]
            for i in range(resource.size(store)):
                ref=resource.get(store,i)
                if isinstance(ref,wt.Func):tags+=1;value=ref(store);assert value in (101,202,999);values.append({101:257,202:258,999:row['proof']['foreignReference']}[value])
                else:values.append(256)
            result[rid]=values
        return result
    assert len(manifest['rows'])==len(node['rows'])
    for row,expected in zip(manifest['rows'],node['rows']):
        if any(x['kind']=='table' for x in row['proof']['resources'].values()):
            funcs=k.p.section(k.p.read(source/row['source']),'func')
            for i,v in enumerate((101,202)):assert [x for x in funcs[i][1:] if x[0] not in k.p.DECL]==[['i32.const',str(v)]]
        compiled=wt.Module(engine,(source/row['prepared']).read_bytes());samples=[]
        for sample in row['samples']:
            words=[sample['witness']['steps']] if sample['witness'] else sample['positiveSequences'];observations=[]
            for word in words:
                with wt.Store(engine) as store:
                    foreign=wt.Instance(store,foreign_module,[]).exports(store)['foreign'];pair=[]
                    for flags in (row['left'],row['right']):
                        instance=wt.Instance(store,compiled,[]).exports(store);patch(store,instance,foreign,row,sample['patches'],False)
                        for i,v in enumerate(flags):
                            if not v:instance['__guard_drop_'+str(i)](store)
                        pair.append(instance)
                    difference=terminal_at=None;executed=0
                    for i,step in enumerate(word):
                        outcomes=[]
                        if step['kind']=='write':
                            for instance in pair:patch(store,instance,foreign,row,step['cells'],True)
                            outcomes=[('write',),('write',)]
                        else:
                            for instance in pair:
                                try:outcomes.append(('return',instance[step['name']](store,*step['args'])))
                                except wt.Trap:outcomes.append(('trap',))
                                calls+=1
                        executed+=1
                        if outcomes[0]!=outcomes[1] or snapshot(store,pair[0],row)!=snapshot(store,pair[1],row):difference=i+1;break
                        if row['proof']['protocol']=='terminal' and outcomes[0][0]=='trap':terminal_at=i+1;terminated+=1;break
                    assert difference==(len(word) if sample['witness'] else None),(row['name'],word)
                    observations.append({'difference':difference,'terminalAt':terminal_at,'executed':executed})
            samples.append({'negative':sample['witness'] is not None,'sequences':observations})
        result={'name':row['name'],'status':row['proof']['status'],'samples':samples};assert result==expected;rows.append(result)
    assert calls==node['apiCalls'] and writes==node['cellWrites'] and terminated==node['terminatedSequences']
    result={'rows':rows,'wasmtime':importlib.metadata.version('wasmtime'),'apiCalls':calls,'cellWrites':writes,'pureReferenceTagCalls':tags,'terminatedSequences':terminated}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('node',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.node,v.out)
