"""Wasmtime control replay: reference tags restricted to verified pure constants."""
import argparse,hashlib,importlib.metadata,itertools,json,shutil,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt
BASE=1<<32
def main(source,out):
    out.mkdir(parents=True,exist_ok=False);m=json.loads((source/'manifest.json').read_text());node=json.loads((source/'results.json').read_text());engine=wt.Engine();rows=[];calls=tagcalls=0
    def snap(store,e,row):
        nonlocal tagcalls
        state={}
        for rid,info in row['proof']['resources'].items():
            resource=e['__guard_resource_'+rid]
            if info['kind']=='memory':state[rid]=bytes(resource.read(store))
            else:
                vals=[]
                for i in range(resource.size(store)):
                    f=resource.get(store,i)
                    if isinstance(f,wt.Func):tagcalls+=1;value=f(store);assert value in (101,202);vals.append({101:257,202:258}[value])
                    else:vals.append(256)
                state[rid]=vals
        return state
    for row,expected in zip(m['rows'],node['rows']):
        original=k.p.read(source/row['source']);funcs=k.p.section(original,'func')
        for i,constant in enumerate([101,202]):assert [x for x in funcs[i][1:] if x[0] not in k.p.DECL]==[['i32.const',str(constant)]]
        compiled=wt.Module(engine,(source/row['prepared']).read_bytes());sequences=[list(x) for n in range(1,m['depth']+1) for x in itertools.product(row['actions'],repeat=n)];samples=[]
        for sample in row['samples']:
            witness=None
            for seq in sequences:
                with wt.Store(engine) as store:
                    pair=[]
                    for alive in (row['left'],row['right']):
                        e=wt.Instance(store,compiled,[]).exports(store)
                        for key,value in sample['patches']:
                            rid,index=divmod(key,BASE);resource=e['__guard_resource_'+str(rid)]
                            if row['proof']['resources'][str(rid)]['kind']=='memory':resource.write(store,bytes([value]),index)
                            else:assert value in (256,257,258);resource.set(store,index,None if value==256 else e['__guard_func_'+str(value-257)])
                        for i,live in enumerate(alive):
                            if not live:e['__guard_drop_'+str(i)](store)
                        pair.append(e)
                    for step,api in enumerate(seq):
                        outcomes=[]
                        for e in pair:
                            try:e[api](store);outcomes.append('return')
                            except wt.Trap:outcomes.append('trap')
                            calls+=1
                        if outcomes[0]!=outcomes[1] or snap(store,pair[0],row)!=snap(store,pair[1],row):witness=seq[:step+1];break
                if witness:break
            assert (witness is None)==sample['satisfies'];samples.append({'satisfies':sample['satisfies'],'witness':witness})
        result={'name':row['name'],'status':row['proof']['status'],'guard':row['proof']['guard'],'samples':samples};assert result==expected;rows.append(result)
    assert calls==node['apiCalls']
    result={'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'apiCalls':calls,'tagCalls':tagcalls,'samples':node['samples'],
      'scope':'Pure constant-return reference tags on these controls, not arbitrary Wasmtime function identity.'}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/Path(__file__).name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if isinstance(v,int)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);v=p.parse_args();main(v.source,v.out)
