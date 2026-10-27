"""Explicit-contract entry point for the restricted restoration diagnosis."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
import prototype as k
HERE=Path(__file__).resolve().parent
def load(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('protocol','guard-protocol.py');f=load('fast','guard-terminal-fast.py')

def store_values(path,model):
    data=json.loads(path.read_text(encoding='utf8'))
    if not isinstance(data,dict) or set(data)!={'cells'} or not isinstance(data['cells'],list):raise ValueError('store must contain only a cells list')
    values={}
    for pair in data['cells']:
        if not isinstance(pair,list) or len(pair)!=2 or any(type(x) is not int for x in pair):raise ValueError('each cell must be [integer location, integer value]')
        key,value=pair
        if key in values:raise ValueError('duplicate store cell')
        if key not in model['cells']:raise ValueError('store cell outside the analysis footprint')
        kind=model['resources'][key//p.c.g.BASE]['kind'];lo,hi=(0,255) if kind=='memory' else (256,256+model['functions'])
        if not lo<=value<=hi:raise ValueError('store cell outside its typed domain')
        values[key]=value
    if set(values)!=set(model['cells']):raise ValueError('store must explicitly provide every footprint cell')
    return values

def diagnose(source,left,right,observation,protocol,store=None):
    k.p.tool('wasm-validate',[source]);module=k.p.read(source)
    try:model=p.c.parse(module)
    except ValueError as e:raise p.c.g.g.Unsupported(str(e)) from e
    values=store_values(store,model) if store else None
    if observation=='returns' and protocol=='terminal':
        result=f.analyse(model,left,right);result['method']='terminal-one-call';proof=None
    else:
        prepared=p.prepare(model,left,right,observation,protocol);proof=prepared['proof'];result={**proof,'method':'relational-fixed-point'}
        result['witness']=p.extract(prepared,values) if values is not None else None
    result['concreteStoreEvaluation']='not-requested' if values is None else 'equal' if result['witness'] is None else 'different'
    result['sourceSha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    result['premises']={'commonInitialMemoryAndTables':True,'fixedMinimumCapacities':True,'externalStateMutation':False,
       'tableObservation':'original-function-index correspondence, not arbitrary function equivalence',
       'scope':'restricted constant bulk APIs plus constant returns and byte read; not all WebAssembly'}
    result['footprint']=model['cells'];return result

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('source',type=Path);a.add_argument('out',type=Path)
    a.add_argument('--left',required=True,help='segment-live bits in parser order (data then elem)');a.add_argument('--right',required=True)
    a.add_argument('--observation',required=True,choices=['full','public','returns']);a.add_argument('--after-trap',required=True,choices=['terminal','reenter']);a.add_argument('--store',type=Path)
    v=a.parse_args()
    if v.out.exists():a.error('output already exists; choose a new path')
    if any(x not in '01' for x in v.left+v.right):a.error('segment bits must be 0 or 1')
    try:result=diagnose(v.source,[x=='1' for x in v.left],[x=='1' for x in v.right],v.observation,v.after_trap,v.store)
    except p.c.g.g.Unsupported as e:result={'status':'unsupported','reason':str(e)}
    except (ValueError,RuntimeError,OSError) as e:result={'status':'invalid-input','reason':str(e)}
    v.out.write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({key:result[key] for key in ('status','method','concreteStoreEvaluation','reason') if key in result}))
    return 0 if result['status'] not in ('unsupported','invalid-input') else 2
if __name__=='__main__':sys.exit(main())
