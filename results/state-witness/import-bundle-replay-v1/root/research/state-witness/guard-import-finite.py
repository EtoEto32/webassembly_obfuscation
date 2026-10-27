"""Concrete finite-domain BFS baseline; no equality maps, SMT, or guard layers.

The parser is shared. Constants plus two fresh values suffice to preserve one
inequality witness for this value-independent copy/constant profile (see note).
"""
import argparse,collections,hashlib,importlib.util,itertools,json,shutil,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('finite_import',HERE/'guard-import.py');i=importlib.util.module_from_spec(s);s.loader.exec_module(i)


def domains(model):
    bykind={'memory':set(),'table':set()}
    for seg in model['segments']:bykind['memory' if seg['kind']=='data' else 'table'].update(seg['values'])
    for action in model['actions']:
        for block in action['blocks']:
            for op in block['ops']:
                if op['kind']=='fill':bykind[model['resources'][op['resource']]['kind']].add(op['value'])
    result={}
    for kind,constants in bykind.items():
        candidates=range(256) if kind=='memory' else itertools.count(256);fresh=[]
        for value in candidates:
            if value not in constants:fresh.append(value)
            if len(fresh)==2:break
        result[kind]=sorted(constants|set(fresh))
    return {cell:result[model['resources'][cell//i.g.BASE]['kind']] for cell in model['cells']}


def block(model,flags,ops,values):
    flags=list(flags);values=values.copy()
    for op in ops:
        kind=op['kind']
        if kind=='drop':flags[op['segment']]=False;continue
        resource,start,length=op['resource'],op['dst'],op['length']
        positions=list(range(start,start+length));bound=model['resources'][resource]['length']
        if start>bound or any(p>=bound for p in positions):return tuple(flags),values,True
        if kind=='init':
            data=model['segments'][op['segment']]['values'] if flags[op['segment']] else []
            source=op['src']
            if source>len(data) or len(data[source:source+length])!=length:return tuple(flags),values,True
            copied=data[source:source+length]
        elif kind=='copy':
            source=op['src'];sr=op['sourceResource'];limit=model['resources'][sr]['length']
            if source>limit or source+length>limit:return tuple(flags),values,True
            copied=[values[sr*i.g.BASE+p] for p in range(source,source+length)]
        elif kind=='fill':copied=[op['value']]*length
        else:raise ValueError(kind)
        for position,value in zip(positions,copied):values[resource*i.g.BASE+position]=value
    return tuple(flags),values,False


def next_boundary(model,action,bi,flags,values):
    b=action['blocks'][bi];flags,values,trap=block(model,flags,b['ops'],values)
    label=('end','trap') if trap else ('end','return') if b['host'] is None else ('host',*b['host'])
    return flags,values,label


def transitions(model,pair,action,values,contract,protocol,alphabet):
    public=[c for c in model['cells'] if c//i.g.BASE in model['publicResources']]
    visible=model['cells'] if contract=='full' else public if contract=='public' else []
    pending=[(0,pair,values,[])];result=[]
    while pending:
        bi,flags,stores,writes=pending.pop()
        step=[next_boundary(model,action,bi,flags[n],stores[n]) for n in (0,1)];labels=[s[2] for s in step]
        lf,lv,_=step[0];rf,rv,_=step[1]
        if labels[0]!=labels[1]:result.append({'different':True,'writes':writes});continue
        if labels[0][0]=='end':
            different=any(lv[c]!=rv[c] for c in visible);terminal=protocol=='terminal' and labels[0][1]=='trap'
            result.append({'different':different,'terminal':terminal,'flags':(lf,rf),'values':(lv,rv),'writes':writes});continue
        summary=model['summaries'][labels[0][1:]]
        if summary['reads']=='public' and any(lv[c]!=rv[c] for c in public):result.append({'different':True,'writes':writes});continue
        if summary['writes']=='none':pending.append((bi+1,(lf,rf),(lv,rv),writes));continue
        for items in itertools.product(*(alphabet[c] for c in public)):
            assignment=dict(zip(public,items));pending.append((bi+1,(lf,rf),({**lv,**assignment},{**rv,**assignment}),writes+[{'block':bi,'cells':sorted(assignment.items())}]))
    return result


def bfs(model,pair,values,contract,protocol,alphabet,limit=20000):
    cells=model['cells']
    def key(flags,stores):return flags+tuple(tuple(s[c] for c in cells) for s in stores)
    queue=collections.deque([(pair,(values,values),[])]);seen={key(pair,(values,values))};count=0
    while queue:
        flags,stores,word=queue.popleft()
        for action in model['actions']:
            for edge in transitions(model,flags,action,stores,contract,protocol,alphabet):
                count+=1;trace=word+[{'name':action['name'],'writes':edge['writes']}]
                if edge['different']:return {'equal':False,'calls':trace,'states':len(seen),'transitions':count}
                if edge['terminal']:continue
                state=key(edge['flags'],edge['values'])
                if state in seen:continue
                seen.add(state)
                if len(seen)>limit:raise i.eq.Unsupported('finite BFS state limit')
                queue.append((edge['flags'],edge['values'],trace))
    return {'equal':True,'calls':None,'states':len(seen),'transitions':count}


def main(source,out):
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for row in json.loads((source/'manifest.json').read_text())['rows']:
        summaries={(s['module'],s['field']):{k:s[k] for k in ('reads','writes')} for s in row['proof']['hostSummaries']}
        model=i.parse(i.k.p.read(source/row['source']),summaries);alphabet=domains(model);proof=row['proof'];prepared=i.prepare(model,row['left'],row['right'],proof['contract'],proof['protocol']);cases=[]
        if len(model['cells'])>3:raise i.eq.Unsupported('exhaustive initial-store bound')
        started=time.perf_counter()
        for vals in itertools.product(*(alphabet[c] for c in model['cells'])):
            values=dict(zip(model['cells'],vals));result=bfs(model,(tuple(row['left']),tuple(row['right'])),values,proof['contract'],proof['protocol'],alphabet)
            assert result['equal']==i.c.holds(prepared['layers'][-1][0],values,values),(row['name'],values,result)
            cases.append({'values':sorted(values.items()),**result})
        rows.append({'name':row['name'],'alphabet':alphabet,'cases':cases,'seconds':time.perf_counter()-started})
    result={'rows':rows,'contracts':len(rows),'initialStores':sum(len(r['cases']) for r in rows),'equal':sum(c['equal'] for r in rows for c in r['cases']),
        'different':sum(not c['equal'] for r in rows for c in r['cases']),'maxStates':max(c['states'] for r in rows for c in r['cases']),
        'transitions':sum(c['transitions'] for r in rows for c in r['cases']),
        'scope':'All common initial stores over constants plus two fresh values, concrete exhaustive finite BFS, shared parser. No fair performance comparison claimed.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    for name in ('guard-import-finite.py','guard-import.py','guard-import-proof.md','guard-environment.py','guard-protocol.py','guard-contract.py','guard-table.py','guard-analysis.py','prototype.py'):shutil.copy2(HERE/name,out/name)
    (out/'sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir()},indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('out',type=Path);v=a.parse_args();main(v.source,v.out)
