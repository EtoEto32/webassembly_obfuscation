"""Lower the shared Wasm model to a generic equality IR and compare all guards."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import time

HERE=Path(__file__).resolve().parent
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
i=load('herbrand_frontend','guard-import.py')
h=load('herbrand_generic','copy-equality.py')
def encode(guard):return None if guard is None else [[list(a),list(b)] for a,b in guard]

def lower(model,left,right,contract,protocol):
    if contract not in ('full','public','returns') or protocol not in ('terminal','reenter'):raise ValueError('Invalid contract')
    for side in (left,right):
        if len(side)!=len(model['segments']):raise ValueError('Invalid segment count')
        if any(flag and not segment['initialLive'] for flag,segment in zip(side,model['segments'])):raise ValueError('Invalid initial lifetime')
    states=[(tuple(left),tuple(right))];lookup={states[0]:0};graph=[]
    public=[cell for cell in model['cells'] if cell//i.g.BASE in model['publicResources']]
    resources=set(model['resources']) if contract=='full' else set(model['publicResources']) if contract=='public' else set()
    observed=[cell for cell in model['cells'] if cell//i.g.BASE in resources]
    equal=lambda cells:tuple((('l',cell),('r',cell)) for cell in cells)
    for pair in states:
        if len(states)>1024:raise ValueError('State bound')
        row=[]
        for action in model['actions']:
            paths=[i.path(model,flags,action) for flags in pair]
            target=tuple(path[-1]['alive'] for path in paths)
            if target not in lookup:lookup[target]=len(states);states.append(target)
            labels=[[event['label'] for event in path] for path in paths]
            if labels[0]!=labels[1]:steps=[{'op':'require','condition':None}]
            else:
                steps=[]
                for left_event,right_event in zip(*paths):
                    mapping={}
                    for side,event in (('l',left_event),('r',right_event)):
                        for cell,(kind,value) in event['mapping'].items():mapping[side,cell]=(side,value) if kind=='m' else (kind,value)
                    steps.append({'op':'parallel','mapping':mapping})
                    if left_event['label'][0]=='host':
                        summary=model['summaries'][left_event['label'][1:]]
                        if summary['reads']=='public':steps.append({'op':'require','condition':equal(public)})
                        if summary['writes']!='none':steps.append({'op':'shared-input','pairs':equal(public),'optional':summary['writes']=='may-public'})
                steps.append({'op':'require','condition':equal(observed)})
            terminal=protocol=='terminal' and labels[0][-1]==labels[1][-1]==('end','trap')
            row.append({'target':None if terminal else lookup[target],'steps':steps})
        graph.append(row)
    return states,graph

def solve(model,left,right,contract,protocol,schedule='sweep'):
    started=time.perf_counter();states,graph=lower(model,left,right,contract,protocol);lowered=time.perf_counter()
    result=h.solve(graph) if schedule=='sweep' else h.solve_worklist(graph)
    common=h.substitute(result['conditions'][0],{(side,cell):('m',cell) for side in ('l','r') for cell in model['cells']})
    proof={'status':'impossible' if common is None else 'conditional' if common else 'unconditional','guard':encode(common),
           'states':[dict(left=list(a),right=list(b),guard=encode(guard)) for (a,b),guard in zip(states,result['conditions'])]}
    return dict(proof=proof,summary=dict(lowerSeconds=lowered-started,seconds=time.perf_counter()-started,
        states=len(states),iterations=result['iterations'],wpCalls=result['wpCalls']))

def main(source,out,schedule='sweep'):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    manifest=json.loads((source/'manifest.json').read_text())
    inputs=manifest['rows'] if 'conditions' not in manifest else [dict(name=row['kind']+'-'+row['writes'],source=row['kind']+'.wasm',proof=row['proof']) for row in manifest['conditions']]
    for row in inputs:
        proof=row['proof'];initial=proof['states'][0]
        summaries={(s['module'],s['field']):{key:s[key] for key in ('reads','writes')} for s in proof['hostSummaries']}
        model=i.parse(i.k.p.read(source/row['source']),summaries,proof.get('continuationOffsets'))
        actual=solve(model,initial['left'],initial['right'],proof['contract'],proof['protocol'],schedule)
        same=all(actual['proof'][key]==proof[key] for key in ('status','guard','states'))
        rows.append(dict(name=row['name'],same=same,**actual))
    summary=dict(contracts=len(rows),sameAllStateConditions=sum(row['same'] for row in rows),
                 differences=[row['name'] for row in rows if not row['same']],rows=rows,
                 sourceManifestSha256=hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest(),
                 sharedFrontend=True,sharedEqualityBackend=False,authorImplementation=False,schedule=schedule)
    (out/'results.json').write_text(json.dumps(summary,indent=2))
    for name in ('guard-herbrand.py','copy-equality.py','guard-herbrand-plan.md','guard-import.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):
        shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},indent=2))
    print(json.dumps({key:value for key,value in summary.items() if key!='rows'}))
    if summary['differences']:raise SystemExit(1)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('out',type=Path);parser.add_argument('--schedule',choices=['sweep','atomic'],default='sweep');args=parser.parse_args();main(args.source,args.out,args.schedule)
