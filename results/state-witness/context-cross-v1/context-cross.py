"""Independent Wasmtime execution of the reconstructed original-API model."""
import argparse,base64,hashlib,importlib.metadata,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt


def main(inputs,node,out):
    out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();engine=wt.Engine();rows=[]
    m=json.loads((inputs/'manifest.json').read_text());reference=json.loads((node/'results.json').read_text())
    def invoke(store,e,n,args=()):
        try:return {'value':e[n](store,*args)}
        except wt.Trap:return {'trap':True}
    def execute(module,c,state,n):
        with wt.Store(engine) as store:
            e=wt.Instance(store,module,[]).exports(store);e['memory'].write(store,base64.b64decode(state['memory']),0)
            tagmap={v:k for k,v in c['tags'].items()};assert len(tagmap)==len(c['tags'])
            for i,values in enumerate(state['tables']):
                t=e['__audit_table_'+str(i)]
                for j,tag in enumerate(values):t.set(store,j,None if tag is None else e['__ctx_func_'+tagmap[tag]])
            for seg,observed in zip(c['observer']['segments'],state['segments']):
                if not seg['observable'] or observed.get('trap'):
                    e[f'__ctx_drop_{seg["kind"]}_{seg["index"]}'](store)
            result=invoke(store,e,n)
            tables=[]
            for i in range(c['tables']):
                t=e['__audit_table_'+str(i)];values=[]
                for j in range(t.size(store)):
                    f=t.get(store,j);values.append(f(store) if isinstance(f,wt.Func) else None)
                tables.append(values)
            successor={'memory':base64.b64encode(e['memory'].read(store,0,c['guestPages']*65536)).decode(),
                       'tables':tables,'segments':[invoke(store,e,s['probe']) if s['probe'] else {'unobservable':True} for s in c['observer']['segments']]}
            return result,successor
    def closure(module,c,profile,left,right):
        if profile['status']!='accepted':return {'status':'unsupported','reason':profile['reason']}
        queue=[(left,right,[])];seen=set();edges=[];index=0
        key=lambda a:json.dumps(a,sort_keys=True)
        while index<len(queue):
            if index>=128:return {'status':'state-bound','nodes':index,'edges':edges}
            a,b,prefix=queue[index];pair=(key(a),key(b));nodeid=index;index+=1
            if a==b or pair in seen:continue
            seen.add(pair)
            for action in profile['actions']:
                if action['kind']=='all-i32-readonly-self-loop':
                    assert a['memory']==b['memory'];edges.append({'node':nodeid,'api':action['name'],'kind':action['kind']});continue
                xo,xs=execute(module,c,a,action['name']);yo,ys=execute(module,c,b,action['name'])
                suffix=prefix+[{'name':action['name'],'args':[]}];om=xo==yo;sm=xs['memory']==ys['memory'] and xs['tables']==ys['tables']
                edges.append({'node':nodeid,'api':action['name'],'baseline':xo,'restored':yo,'outcomeMatches':om,'guestStateMatches':sm})
                if not om or not sm:return {'status':'witness','nodes':len(seen),'edges':edges,'witness':suffix}
                queue.append((xs,ys,suffix))
        return {'status':'closed-original-api-model','nodes':len(seen),'edges':edges}
    for item in m['cases']:
        c=item['case'];module=wt.Module(engine,(inputs/item['normalized']).read_bytes())
        for expected in [r for r in reference['rows'] if r['id']==c['id']]:
            states=json.loads((node/expected['stateFile']).read_text())
            result=closure(module,c,item['finiteProfile'],states['baseline'],states['restored'])
            assert result==expected['finiteClosure'],(c['id'],expected['stopAt'],result,expected['finiteClosure'])
            rows.append({'id':c['id'],'stopAt':expected['stopAt'],'finiteClosure':result,'matchesNode':True})
    result={'wasmtime':importlib.metadata.version('wasmtime'),'seconds':time.perf_counter()-start,
            'note':'Replays the finite transition model; does not repeat the bounded suffix enumeration.',
            'summary':{'scenarios':len(rows),'closedModels':sum(r['finiteClosure']['status']=='closed-original-api-model' for r in rows),
                       'witnesses':sum(r['finiteClosure']['status']=='witness' for r in rows)},'rows':rows}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/'context-cross.py')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(result['summary']))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('inputs',type=Path);a.add_argument('node',type=Path);a.add_argument('out',type=Path)
    v=a.parse_args();main(v.inputs,v.node,v.out)
