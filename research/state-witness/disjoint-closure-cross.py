"""Independent finite-model replay; table references restricted to unique constant tags."""
import argparse,base64,hashlib,importlib.metadata,json,shutil,sys
from pathlib import Path
import prototype as k
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt

def main(spec_source,source,node,out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();rows=[]
    m=json.loads((source/'manifest.json').read_text());profiles=json.loads((node/'profiles.json').read_text());reference=json.loads((node/'results.json').read_text())
    def call(s,e,name):
        try:return {'value':e[name](s)}
        except wt.Trap:return {'trap':True}
    def operate(module,c,tags,state=None,drop=None,action=None):
        meta=c['observer']
        with wt.Store(engine) as s:
            e=wt.Instance(s,module,[]).exports(s)
            if state:
                if meta['memory']:e['__sw_memory'].write(s,base64.b64decode(state['memory']),0)
                for i,values in enumerate(state['tables']):
                    table=e['__sw_table'+('_'+str(i) if i else '')]
                    for j,idx in enumerate(values):table.set(s,j,None if idx is None else e['__sw_func_'+str(idx)])
                for seg,obs in zip(meta['segments'],state['segments']):
                    if seg['initialLive'] and obs.get('trap'):e[f'__ctx_drop_{seg["kind"]}_{seg["index"]}'](s)
            if drop:e[f'__ctx_drop_{drop["kind"]}_{drop["index"]}'](s)
            outcome=call(s,e,action) if action else None;tables=[]
            for i in range(meta['tableCount']):
                table=e['__sw_table'+('_'+str(i) if i else '')];values=[]
                for j in range(table.size(s)):
                    f=table.get(s,j);values.append(tags[f(s)] if isinstance(f,wt.Func) else None)
                tables.append(values)
            snap={'tables':tables,'segments':[call(s,e,seg['probe']) if seg['probe'] else {'unobservable':True} for seg in meta['segments']]}
            if meta['memory']:snap['memory']=base64.b64encode(e['__sw_memory'].read(s)).decode()
            return outcome,snap
    for c in m['cases']:
        profile=profiles[c['source']];module=wt.Module(engine,(source/c['file']).read_bytes());tags={}
        if profile['status']=='accepted':
            original=k.p.read(spec_source/c['source']);funcs=k.p.section(original,'func')
            refs={int(x) for seg in k.p.section(original,'elem') for x in seg[seg.index('func')+1:]}
            for i in sorted(refs):
                body=[n for n in funcs[i][1:] if n[0] not in k.p.DECL]
                assert len(body)==1 and body[0][0]=='i32.const','Cannot classify arbitrary function references'
                value=int(body[0][1]);assert value not in tags,'Ambiguous constant tag';tags[value]=i
        for target in c['segments']:
            seg={'kind':target['segment']['kind'],'index':target['segment']['index']}
            expected=next(r['result'] for r in reference['rows'] if r['source']==c['source'] and r['segment']==seg)
            if profile['status']!='accepted':result={'status':'unsupported','reason':profile['reason']}
            else:
                a=operate(module,c,tags)[1];b=operate(module,c,tags,drop=seg)[1]
                queue=[(a,b,[])];seen=set();edges=[];at=0;result=None
                while at<len(queue):
                    if at>=128:result={'status':'state-bound','nodes':len(seen),'edges':edges};break
                    left,right,prefix=queue[at];idx=at;at+=1
                    pair=json.dumps([left,right],sort_keys=True)
                    if left==right or pair in seen:continue
                    seen.add(pair)
                    for action in profile['actions']:
                        name=action['name']
                        if action['kind']=='all-i32-readonly-self-loop':
                            assert left['memory']==right['memory'];edges.append({'node':idx,'api':name,'kind':action['kind']});continue
                        ao,an=operate(module,c,tags,left,action=name);bo,bn=operate(module,c,tags,right,action=name);diff=[]
                        if an.get('memory')!=bn.get('memory'):diff.append('memory')
                        for i,(x,y) in enumerate(zip(an['tables'],bn['tables'])):
                            if x!=y:diff.append('table'+('_'+str(i) if i else ''))
                        if an['segments']!=bn['segments']:diff.append('segments')
                        edges.append({'node':idx,'api':name,'baseline':ao,'changed':bo,'stateDifferences':diff})
                        suffix=prefix+[name]
                        if ao!=bo:result={'status':'api-witness','witness':suffix,'nodes':len(seen),'edges':edges};break
                        if any(x!='segments' for x in diff):result={'status':'unresolved-store-divergence','nodes':len(seen),'edges':edges};break
                        queue.append((an,bn,suffix))
                    if result:break
                if result is None:result={'status':'closed-original-api-model','nodes':len(seen),'edges':edges}
            # Difference categories form a set; observer insertion order differs.
            for edge in result.get('edges',[]):
                if 'stateDifferences' in edge:edge['stateDifferences'].sort()
            normalized_expected=json.loads(json.dumps(expected))
            for edge in normalized_expected.get('edges',[]):
                if 'stateDifferences' in edge:edge['stateDifferences'].sort()
            assert result==normalized_expected,(c['source'],seg,result,normalized_expected)
            rows.append({'source':c['source'],'segment':seg,'matchesNode':True,'result':result})
    result={'wasmtime':importlib.metadata.version('wasmtime'),'summary':reference['summary'],'rows':rows,
            'scope':'Finite-profile models only; table identity via statically checked unique constant-return functions.'}
    (out/'results.json').write_text(json.dumps(result,indent=2));shutil.copy2(__file__,out/'disjoint-closure-cross.py')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2));print(json.dumps(result['summary']))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('spec',type=Path);p.add_argument('source',type=Path);p.add_argument('node',type=Path);p.add_argument('out',type=Path)
    v=p.parse_args();main(v.spec,v.source,v.node,v.out)
