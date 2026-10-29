"""Known atomic-obligation worklist scheduling for the restricted equality WP."""
import argparse,collections,hashlib,importlib.util,json,shutil,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('worklist_imports',HERE/'guard-import.py');i=importlib.util.module_from_spec(s);s.loader.exec_module(i)


def solve(model,left,right,contract,protocol,max_facts=250000):
    started=time.perf_counter()
    if contract not in ('full','public','returns') or protocol not in ('terminal','reenter'):raise ValueError('invalid contract')
    for side in (left,right):
        if len(side)!=len(model['segments']):raise ValueError('segment state length')
        if any(x and not seg['initialLive'] for x,seg in zip(side,model['segments'])):raise ValueError('invalid live segment')
    states=[(tuple(left),tuple(right))];index={states[0]:0};edges=[]
    for pair in states:
        if len(states)>1024:raise i.eq.Unsupported('state-pair bound')
        row=[]
        for action in model['actions']:
            paths=[i.path(model,pair[n],action) for n in (0,1)];target=tuple(p[-1]['alive'] for p in paths)
            if target not in index:index[target]=len(states);states.append(target)
            row.append({'action':action['name'],'paths':paths,'target':index[target]})
        edges.append(row)
    incoming=[[] for _ in states]
    for origin,row in enumerate(edges):
        for edge in row:incoming[edge['target']].append((origin,edge))
    facts=[set() for _ in states];bottom=set();queue=collections.deque();added=wp_calls=0
    def insert(state,condition):
        nonlocal added
        if state in bottom:return
        if condition is None:
            bottom.add(state);facts[state].clear();queue.append((state,None));return
        for atom in sorted(condition):
            if atom not in facts[state]:facts[state].add(atom);queue.append((state,atom));added+=1
        if added>max_facts:raise i.eq.Unsupported('atomic worklist fact bound')
    for origin,row in enumerate(edges):
        for edge in row:
            insert(origin,i.transform(model,edge,frozenset(),contract,protocol));wp_calls+=1
    rounds=0
    while True:
        while queue:
            state,atom=queue.popleft()
            if state in bottom and atom is not None:continue
            for origin,edge in incoming[state]:
                if origin in bottom:continue
                insert(origin,i.transform(model,edge,None if atom is None else frozenset([atom]),contract,protocol));wp_calls+=1
        # Individual atoms can jointly contradict (e.g. x=1 and x=2).
        # Propagate that contradiction before declaring a fixed point.
        guards=[None if n in bottom else i.eq.canonical(atoms) for n,atoms in enumerate(facts)];rounds+=1
        for state,guard in enumerate(guards):
            if guard is None and state not in bottom:insert(state,None)
        if not queue:break
    final=guards[0]
    common=i.eq.canonical([(('m',a[1]) if a[0] in ('l','r') else a,('m',b[1]) if b[0] in ('l','r') else b) for a,b in final]) if final is not None else None
    proof={'status':'impossible' if common is None else 'conditional' if common else 'unconditional','guard':i.c.serial(common),
        'states':[{'left':list(l),'right':list(r),'guard':i.c.serial(v)} for (l,r),v in zip(states,guards)]}
    return {'proof':proof,'guards':guards,'edges':edges,'summary':{'seconds':time.perf_counter()-started,'states':len(states),'factsInserted':added,'wpCalls':wp_calls,'canonicalRounds':rounds,
        'rankLayersGenerated':False,'method':'atomic-obligation worklist; shared parser and equality WP'}}


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for row in json.loads((source/'manifest.json').read_text())['rows']:
        proof=row['proof'];summaries={(r['module'],r['field']):{k:r[k] for k in ('reads','writes')} for r in proof['hostSummaries']}
        model=i.parse(i.k.p.read(source/row['source']),summaries,proof.get('continuationOffsets'));initial=proof['states'][0]
        try:
            result=solve(model,initial['left'],initial['right'],proof['contract'],proof['protocol'])
            same=all(result['proof'][k]==proof[k] for k in ('status','guard','states'))
            record={'name':row['name'],'status':'same-conditions' if same else 'different-conditions',**result}
            record.pop('guards');record.pop('edges')
        except i.eq.Unsupported as err:record={'name':row['name'],'status':'unsupported','reason':str(err)}
        rows.append(record)
    result={'rows':rows,'contracts':len(rows),'statuses':{v:sum(r['status']==v for r in rows) for v in sorted({r['status'] for r in rows})}}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-import-worklist.py','guard-import-worklist-plan.md','guard-import.py','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
