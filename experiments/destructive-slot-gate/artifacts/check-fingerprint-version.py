import collections
import hashlib
import importlib.util
import json
import platform
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE.parent / 'sha-history-gate/check.py'
spec = importlib.util.spec_from_file_location('reference', REF)
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
MASK = 2**32-1


def circuit():
    nodes = []
    def op(name, *args):
        nodes.append([name, list(args)])
        return 9+len(nodes)-1
    def sigma(x, rotations):
        a,b,c = [op('r'+str(n), x) for n in rotations]
        return op('xor', op('xor', a,b),c)
    a,b,c,d,e,f,g,h,u = range(9)
    ch = op('xor', op('and',e,f), op('and',op('not',e),g))
    maj = op('xor',op('xor',op('and',a,b),op('and',a,c)),op('and',b,c))
    t1 = op('add',op('add',op('add',h,sigma(e,(6,11,25))),ch),u)
    t2 = op('add',sigma(a,(2,13,22)),maj)
    outputs = [op('add',t1,t2),a,b,c,op('add',d,t1),e,f,g]
    return nodes,outputs


def schedule(nodes, outputs, seed):
    rng = random.Random(seed)
    uses = collections.Counter(outputs)
    for _,args in nodes: uses.update(args)
    live = {i:i for i in range(9)}
    free = []
    pending = set(range(9,9+len(nodes)))
    code = []
    slots = 9
    while pending:
        ready = sorted(i for i in pending if all(a in live for a in nodes[i-9][1]))
        i = rng.choice(ready)
        name,args = nodes[i-9]
        src = [live[a] for a in args]
        # Reads precede writes, permitting destructive reuse of a dying operand.
        for a in args:
            uses[a] -= 1
            if uses[a] == 0: free.append(live.pop(a))
        if free:
            dst = free.pop(rng.randrange(len(free)))
        else:
            dst = slots
            slots += 1
        code.append([name, src, dst])
        live[i] = dst
        pending.remove(i)
    return {'code':code,'outputs':[live[i] for i in outputs],'slots':slots}


def recover(program):
    # Only public input-slot mapping and emitted physical instructions are used.
    current = {i:i for i in range(9)}
    nodes = []
    for name,src,dst in program['code']:
        args = [current[a] for a in src]
        nodes.append([name,args])
        current[dst] = 9+len(nodes)-1
    return nodes,[current[a] for a in program['outputs']]


def apply(name, args):
    if name == 'add': return (args[0]+args[1]) & MASK
    if name == 'xor': return args[0]^args[1]
    if name == 'and': return args[0]&args[1]
    if name == 'not': return args[0]^MASK
    n = int(name[1:])
    return ((args[0]>>n)|(args[0]<<(32-n))) & MASK


def evaluate(nodes,outputs,inputs):
    vals = list(inputs)
    for name,args in nodes: vals.append(apply(name,[vals[a] for a in args]))
    return [vals[i] for i in outputs]


def execute(program,inputs):
    slots = list(inputs)+[None]*(program['slots']-9)
    for name,src,dst in program['code']:
        args = [slots[a] for a in src]
        slots[dst] = apply(name,args)
    return [slots[a] for a in program['outputs']]


def fingerprints(nodes,outputs):
    # Canonical hashes preserve operand order and sharing-independent expression identity.
    values = [hashlib.sha256(f'input:{i}'.encode()).hexdigest() for i in range(9)]
    for name,args in nodes:
        values.append(hashlib.sha256(json.dumps([name,[values[a] for a in args]]).encode()).hexdigest())
    return [values[i] for i in outputs]


def main():
    out = Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'artifacts'
    out.mkdir(parents=True,exist_ok=False)
    plan = json.loads((HERE/'protocol.json').read_text())
    nodes,outputs = circuit()
    rng = random.Random(619742)
    inputs = [[0]*9,[MASK]*9]
    for j in range(9):
        for v in (1,1<<31,MASK):
            row=[0]*9;row[j]=v;inputs.append(row)
    inputs += [[rng.getrandbits(32) for _ in range(9)] for _ in range(256)]
    reports=[]
    for seed in plan['seeds']:
        program=schedule(nodes,outputs,seed)
        recovered,ends=recover(program)
        assert fingerprints(nodes,outputs)==fingerprints(recovered,ends)
        negative=0
        samples=[]
        for row in inputs:
            expected=ref.reference(row[:8],row[8])
            actual=execute(program,row)
            decoded=evaluate(recovered,ends,row)
            assert expected==actual==decoded==evaluate(nodes,outputs,row)
            wrong=evaluate(recovered,[0]+ends[1:],row)
            negative += wrong!=expected
            samples.append({'input':row,'expected':expected,'physical':actual,'recovered':decoded})
        assert negative>0
        writes=[i[2] for i in program['code']]
        reuse=sum(n-1 for n in collections.Counter(list(range(9))+writes).values())
        assert reuse>0
        report={'seed':seed,'program':program,'recovered_nodes':recovered,'recovered_outputs':ends,
                'slot_reuses':reuse,'checks':len(inputs),'negative_detected':negative,'mismatches':0}
        reports.append(report)
        (out/f'{seed}-samples.json').write_text(json.dumps(samples)+'\n')
    result={'python':platform.python_version(),'before_nodes':nodes,'before_outputs':outputs,
            'variants':reports,'cases_per_variant':len(inputs),'total_checks':len(inputs)*len(reports),
            'source_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'protocol.json',REF]}}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'nodes':len(nodes),'cases':len(inputs),'total_checks':result['total_checks'],
                      'variants':[{k:r[k] for k in ('seed','slot_reuses','negative_detected')} for r in reports]},indent=2))


if __name__=='__main__': main()
