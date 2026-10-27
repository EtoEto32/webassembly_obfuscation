"""Independent engine/host replication of the generated checkpoint matrix."""
import argparse,hashlib,importlib.metadata,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'))
import wasmtime as wt

def main(source,node_results,out):
    out.mkdir(parents=True,exist_ok=False);engine=wt.Engine();manifest=json.loads((source/'manifest.json').read_text());rows=[]
    js="""import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';
const d=process.argv[1],{extractMeta}=await import(pathToFileURL(path.join(d,'weave.mjs'))),m=JSON.parse(fs.readFileSync(path.join(d,'manifest.json')));
console.log(JSON.stringify(Object.fromEntries(m.cases.flatMap(c=>c.entries).filter(x=>x.backend==='weave'&&x.status==='valid').map(x=>[x.output,extractMeta(fs.readFileSync(path.join(d,x.output)))]))));"""
    r=subprocess.run(['node','--input-type=module','-e',js,str(source.resolve())],capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stderr;metas=json.loads(r.stdout)
    def module(n):return wt.Module(engine,(source/n).read_bytes())
    def invoke(s,e,n):
        try:e[n](s);return {'value':None}
        except wt.Trap:return {'trap':True}
    def segment(s,e,c):return [invoke(s,e,x['probe']) if x['probe'] else {'unobservable':True} for x in c['observer']['segments']]
    def capture(s,e,c,observed):
        memory=bytes(e['memory'].read(s,0,c['guestPages']*65536));tables=[]
        for t in range(c['tables']):
            table=e['__audit_table_'+str(t)];tags=[]
            for i in range(table.size(s)):
                f=table.get(s,i)
                if isinstance(f,wt.Func):
                    v=f(s);assert v in c['tags'].values();tags.append(v)
                else:tags.append(None)
            tables.append(tags)
        return {'memory':memory,'tables':tables,'segments':segment(s,e,c) if observed else None}
    def compare(a,b):return {'guestMemory':a['memory']==b['memory'],'tableTags':a['tables']==b['tables'],'segments':a['segments']==b['segments']}
    def view(a):return {**a,'memory':{'bytes':len(a['memory']),'sha256':hashlib.sha256(a['memory']).hexdigest()}}
    def make(mod,backend,meta,stop,saved=None):
        s=wt.Store(engine);state={'polls':0,'requested':False}
        def poll():
            n=state['polls'];state['polls']+=1
            b=stop>=0 and (n>=stop if backend=='weave' else n==stop);state['requested']|=b;return int(b)
        imports=[wt.Func(s,wt.FuncType([],[wt.ValType.i32()]),poll)]
        if backend=='migrate':
            def restore(caller):
                if saved:
                    for n,b in saved[0].items():caller.get(n).write(caller,b,0)
            imports.append(wt.Func(s,wt.FuncType([],[]),restore,access_caller=True))
        e=wt.Instance(s,mod,imports).exports(s)
        if backend=='weave':
            if saved:
                for n,b in saved[0].items():
                    mem=e[n];delta=len(b)//65536-mem.size(s)
                    if delta>0:mem.grow(s,delta)
                    mem.write(s,b,0)
                for n,v in saved[1].items():e[n].set_value(s,v)
            else:e['__weave_init'](s)
        return s,e,state
    def execute(s,e,n,backend):
        result=invoke(s,e,n)
        if backend=='weave' and not result.get('trap') and e['__weave_flag'].value(s)==1:return {'held':True}
        return result
    node=json.loads((node_results/'results.json').read_text())
    for c in manifest['cases']:
        expected={}
        for kind,orig,cut in [('plain',c['original'],c['cut']),('observed',c['originalObserved'],c['observed'])]:
            states=[]
            for filename in (orig,cut):
                with wt.Store(engine) as s:
                    e=wt.Instance(s,module(filename),[]).exports(s);outcome=invoke(s,e,c['entry']);snap=capture(s,e,c,kind=='observed')
                    states.append((outcome,snap))
            assert states[0]==states[1];expected[kind]={'outcome':states[0][0],'state':states[0][1]}
        for item in c['entries']:
            backend=item['backend'];observed=item['kind']=='observed'
            row={'id':c['id'],'source':c['source'],'operation':c['operation'],'backend':backend,'kind':item['kind'],'transformStatus':item['status']}
            if item['status']!='valid':rows.append(row);continue
            mod=module(item['output']);meta=metas.get(item['output']);baseline=expected[item['kind']]
            s,e,stats=make(mod,backend,meta,-1);co=execute(s,e,c['entry'],backend);count=stats['polls'];cs=capture(s,e,c,observed);s.close()
            row.update({'expected':baseline['outcome'],'expectedState':view(baseline['state']),'continuous':co,
                        'continuousState':view(cs),'continuousComparison':compare(baseline['state'],cs),'polls':count,'scenarios':[]})
            if co!=baseline['outcome'] or not all(row['continuousComparison'].values()):row['status']='continuous-mismatch';rows.append(row);continue
            row['status']='executed'
            for stop in range(count+1):
                a,ae,ast=make(mod,backend,meta,stop);first=execute(a,ae,c['entry'],backend)
                held=first.get('held',False) if backend=='weave' else ast['requested']
                if not held:row['scenarios'].append({'stopAt':stop,'status':'checkpoint-not-reached','outcome':first});a.close();continue
                names=meta['memories'] if backend=='weave' else ['memory','checkpoint_memory']
                saved=({n:bytes(ae[n].read(a)) for n in names},{n:ae[n].value(a) for n in meta['controlGlobals']} if meta else {})
                cp=None
                if observed:
                    before=segment(a,ae,c);z,ze,_=make(mod,backend,meta,-1,saved);after=segment(z,ze,c);z.close()
                    cp={'source':before,'restored':after,'matches':before==after}
                b,be,_=make(mod,backend,meta,-1,saved)
                outcome=execute(b,be,'__weave_resume' if backend=='weave' else c['entry'],backend);snap=capture(b,be,c,observed)
                row['scenarios'].append({'stopAt':stop,'status':'restored','firstOutcome':first,'outcome':outcome,'state':view(snap),
                  'entryMatches':outcome==baseline['outcome'],'comparison':compare(baseline['state'],snap),'checkpointSegments':cp})
                a.close();b.close()
            rows.append(row)
    result={'wasmtime':importlib.metadata.version('wasmtime'),'rows':rows,'matchesNode':rows==node['rows'],
            'sourceManifestHash':hashlib.sha256((source/'sha256.json').read_bytes()).hexdigest(),
            'nodeResultHash':hashlib.sha256((node_results/'sha256.json').read_bytes()).hexdigest()}
    (out/'results.json').write_text(json.dumps(result,indent=2));(out/'metadata.json').write_text(json.dumps(metas,indent=2))
    shutil.copy2(__file__,out/'cut-cross.py')
    (out/'sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()},indent=2))
    assert result['matchesNode'],'independent engine comparison mismatch; full results saved'
    print(json.dumps({'rows':len(rows),'matchesNode':True}))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('node_results',type=Path);a.add_argument('out',type=Path)
    v=a.parse_args();main(v.source,v.node_results,v.out)
