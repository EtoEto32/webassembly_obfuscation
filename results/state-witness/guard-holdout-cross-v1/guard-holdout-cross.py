"""Independent runtime replay of prospective mixed-resource contract tests."""
import argparse,hashlib,importlib.metadata,json,shutil,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
BASE=1<<32

def main(source,out):
    out.mkdir(parents=True,exist_ok=False);manifest=json.loads((source/'manifest.json').read_text());node=json.loads((source/'results.json').read_text());engine=wt.Engine();rows=[];calls=tags=terminated=0
    def snapshot(store,e,row):
        nonlocal tags
        result={}
        for rid in row['proof']['observedResources']:
            x=e['__guard_resource_'+str(rid)];info=row['proof']['resources'][str(rid)]
            if info['kind']=='memory':result[rid]=bytes(x.read(store));continue
            values=[]
            for i in range(x.size(store)):
                f=x.get(store,i)
                if isinstance(f,wt.Func):tags+=1;value=f(store);assert value in (101,202);values.append({101:257,202:258}[value])
                else:values.append(256)
            result[rid]=values
        return result
    for row,expected in zip(manifest['rows'],node['rows']):
        if any(x['kind']=='table' for x in row['proof']['resources'].values()):
            funcs=k.p.section(k.p.read(source/row['source']),'func')
            for i,v in enumerate((101,202)):assert [x for x in funcs[i][1:] if x[0] not in k.p.DECL]==[['i32.const',str(v)]]
        compiled=wt.Module(engine,(source/row['prepared']).read_bytes());samples=[]
        for sample in row['samples']:
            sequences=[sample['witness']['calls']] if sample['witness'] else sample['positiveSequences'];observations=[]
            for sequence in sequences:
                with wt.Store(engine) as store:
                    pair=[]
                    for flags in (row['left'],row['right']):
                        e=wt.Instance(store,compiled,[]).exports(store)
                        for key,value in sample['patches']:
                            rid,index=divmod(key,BASE);x=e['__guard_resource_'+str(rid)]
                            if row['proof']['resources'][str(rid)]['kind']=='memory':x.write(store,bytes([value]),index)
                            else:assert value in (256,257,258);x.set(store,index,None if value==256 else e['__guard_func_'+str(value-257)])
                        for i,v in enumerate(flags):
                            if not v:e['__guard_drop_'+str(i)](store)
                        pair.append(e)
                    difference=terminal_at=None;executed=0
                    for i,call in enumerate(sequence):
                        outcomes=[]
                        for e in pair:
                            try:outcomes.append(('return',e[call['name']](store,*call['args'])))
                            except wt.Trap:outcomes.append(('trap',))
                            calls+=1
                        executed+=1
                        if outcomes[0]!=outcomes[1] or snapshot(store,pair[0],row)!=snapshot(store,pair[1],row):difference=i+1;break
                        if row['proof']['protocol']=='terminal' and outcomes[0][0]=='trap':terminal_at=i+1;terminated+=1;break
                    assert difference==(len(sequence) if sample['witness'] else None)
                    if sample['witness']:assert executed==len(sequence)
                    observations.append({'difference':difference,'terminalAt':terminal_at,'executed':executed})
            samples.append({'negative':sample['witness'] is not None,'sequences':observations})
        result={'name':row['name'],'contract':row['proof']['contract'],'status':row['proof']['status'],'samples':samples};assert result==expected;rows.append(result)
    assert calls==node['apiCalls'] and terminated==node['terminatedSequences'];result={'rows':rows,'wasmtime':importlib.metadata.version('wasmtime'),'apiCalls':calls,'pureReferenceTagCalls':tags,'terminatedSequences':terminated}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.out)
