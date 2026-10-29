"""Attacker: consumes only public tensor DAG, no generator import or secret labels."""
import json, sys, time, hashlib
from pathlib import Path
start=time.perf_counter()
source=Path(sys.argv[1]); destination=Path(sys.argv[2])
if destination.exists(): raise SystemExit('Refuse overwrite')
blob=source.read_bytes(); p=json.loads(blob); modulus=p['modulus']
support={}; recovered=[]; evals=0
for item in p['inputs']:
    support[item['id']]=[tuple(c) for c in item['columns']]
    if len(set(support[item['id']]))!=2: raise ValueError('Noninjective public input')
for item in p['constants']: support[item['id']]=[tuple(item['value'])]
pending={n['id']:n for n in p['nodes']}
while pending:
    ready=[n for n in pending.values() if all(parent in support for parent in n['parents'])]
    if not ready: raise ValueError('Cycle or missing parent')
    for n in ready:
        left,right=(support[v] for v in n['parents']); values=[]; table=[]
        for a in left:
            row=[]
            for b in right:
                # Generic eight-coefficient evaluator, not gate recognition.
                v=tuple(sum(n['tensor'][r][2*i+j]*a[i]*b[j] for i in range(2) for j in range(2))%modulus for r in range(2))
                evals+=1
                if v not in values: values.append(v)
                row.append(values.index(v))
            table.append(row)
        if len(values)>2:
            destination.write_text(json.dumps({'status':'outside-two-state-model','node':n['id'],'support_size':len(values),'tensor_evaluations':evals}))
            raise SystemExit(0)
        support[n['id']]=values
        recovered.append({'id':n['id'],'parents':n['parents'],'table':table,'states':len(values)})
        del pending[n['id']]
outputs=[]
for output in p['outputs']:
    values=[sum(a*b for a,b in zip(output['decoder'],v))%modulus for v in support[output['id']]]
    if any(v not in (0,1) for v in values): raise ValueError('Non-Boolean decoded boundary')
    outputs.append({'id':output['id'],'table':values})
result={'status':'reconstructed','inputs':[n['id'] for n in p['inputs']],'constants':{n['id']:0 for n in p['constants']},'nodes':recovered,'outputs':outputs,'support':{k:list(v) for k,v in support.items()},'tensor_evaluations':evals,'seconds':time.perf_counter()-start,'public_sha256':hashlib.sha256(blob).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
destination.write_text(json.dumps(result,indent=2))
