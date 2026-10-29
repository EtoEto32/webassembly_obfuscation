"""Enumerate typed heap requests, emit real Wasm and check identities on 3 engines."""
import argparse,collections,itertools,json,random,shutil,subprocess,sys,time
from pathlib import Path
from realize import ROOT,HERE,generate,enumerated,validate_graph,Impossible,Unsupported,Budget,type_text,read
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
import hashlib
CHECKER=ROOT/'.tools/gc-witness-target/release/gc-witness-types.exe'
def dump(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def model(kind,mutable,nullable):return dict(types=[dict(kind=kind,fields=[dict(mutable=mutable,value=dict(ref=dict(index=0),nullable=nullable))])],groups=[dict(start=0,length=1)])

def fixtures():
    for kind in ['array','struct']:
        for mutable in [False,True]:
            for nullable in [False,True]:
                m=model(kind,mutable,nullable);base='%s-m%d-n%d'%(kind,mutable,nullable)
                for n in [1,2,3]:
                    vals=[[dict(node=i)] for i in range(n)]
                    if nullable:vals+=[[None]]
                    if kind=='array':vals+=[[]]
                    for index,assignment in enumerate(itertools.product(vals,repeat=n)):
                        yield dict(name=base+'-%d-%d'%(n,index),model=m,nodes=[dict(type=0,values=v) for v in assignment])
    # Two mutually recursive types, with independent field mutability.
    for sm in [False,True]:
        for am in [False,True]:
            m=dict(types=[dict(kind='struct',fields=[dict(mutable=sm,value=dict(ref=dict(index=1),nullable=False))]),dict(kind='array',fields=[dict(mutable=am,value=dict(ref=dict(index=0),nullable=False))])],groups=[dict(start=0,length=2)])
            for a,b,c,d in itertools.product([1,3],[None,0,2],[1,3],[None,0,2]):
                nodes=[dict(type=0,values=[dict(node=a)]),dict(type=1,values=[] if b is None else [dict(node=b)]),dict(type=0,values=[dict(node=c)]),dict(type=1,values=[] if d is None else [dict(node=d)])]
                yield dict(name='mixed-%d-%d-%s-%s-%s-%s'%(sm,am,a,b,c,d),model=m,nodes=nodes)
    # Packed values plus shared children, independent of references-only templates.
    m=dict(types=[dict(kind='struct',fields=[dict(mutable=False,value=dict(scalar='i8')),dict(mutable=True,value=dict(scalar='i16')),dict(mutable=False,value=dict(scalar='i64'))])],groups=[dict(start=0,length=1)])
    yield dict(name='packed-boundaries',model=m,nodes=[dict(type=0,values=[-1,65535,-9223372036854775808]),dict(type=0,values=[127,-32768,9223372036854775807])])

def main(out):
    out.mkdir(parents=True,exist_ok=False);rows=[];cases=[];files=[];expected={};errors=[];enum_states=0;typecache={}
    for fx in fixtures():
        m=fx['model'];key=json.dumps(m,sort_keys=True)
        if key not in typecache:
            file=out/('types-%d.wasm'%len(typecache));wat='(module '+type_text(m)+')';file.write_bytes(wt.wat2wasm(wat));file.with_suffix('.wat').write_text(wat);parsed=read(file)
            if parsed['types']!=m['types']:errors.append(dict(kind='type-parse',name=fx['name']))
            typecache[key]=file.name
        fx['type_file']=typecache[key];validate_graph(m,fx['nodes']);reachable,states=enumerated(m,fx['nodes']);enum_states+=states;fx['enumeration']=dict(reachable=reachable,states=states);cases.append(fx)
        for mode in ['staged','dfs-staged','all-deps','null-patch']:
            r=dict(name=fx['name'],mode=mode,expected=reachable)
            try:
                g=generate(m,fx['nodes'],mode);file=out/(fx['name']+'-'+mode+'.wasm');file.write_bytes(wt.wat2wasm(g.pop('wat')));r.update(status='generated',file=file.name,bytes=file.stat().st_size,**g);files.append(file.name);expected[file.name]=1
                if not reachable:errors.append(dict(kind='constructed-impossible',name=fx['name'],mode=mode))
            except (Impossible,Unsupported,Budget) as e:
                r.update(status=type(e).__name__,reason=str(e))
                if reachable and mode in ['staged','dfs-staged']:errors.append(dict(kind='missed',name=fx['name'],mode=mode))
            rows.append(r)
    # Mutants deliberately violate exact alias identity or a deferred field.
    controls=[('missing-write',model('array',True,False),[dict(type=0,values=[dict(node=0)])],'omit-patches'),('merged-distinct',model('array',True,False),[dict(type=0,values=[]),dict(type=0,values=[])],'merge-final')]
    for name,m,nodes,fault in controls:
        g=generate(m,nodes,fault=fault);file=out/(name+'.wasm');file.write_bytes(wt.wat2wasm(g['wat']));file.with_suffix('.wat').write_text(g['wat']);files.append(file.name);expected[file.name]=0
    dump(out/'cases.json',cases);dump(out/'generation.json',rows);dump(out/'expected.json',expected);dump(out/'request.json',dict(directory=str(out.resolve()),files=files))
    engine_rows=[]
    for name,cmd in [('node',['node',str(ROOT/'research/gc-witness/run.cjs'),str(out/'request.json')]),('spidermonkey',[str(ROOT/'.tools/spidermonkey-150.0.1/js.exe'),'--wasm-compiler=baseline+ion',str(ROOT/'research/gc-witness/run-sm.js'),str(out/'request.json')])]:
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=90);dump(out/(name+'-process.json'),dict(code=cp.returncode,stderr=cp.stderr));assert cp.returncode==0
        obj=json.loads(cp.stdout);dump(out/(name+'.json'),obj);engine_rows += [dict(engine=name,**r) for r in obj['rows']]
    engine=wt.Engine();wr=[]
    for file in files:
        phase='compilation';start=time.perf_counter_ns()
        try:
            module=wt.Module(engine,(out/file).read_bytes());phase='instantiation';store=wt.Store(engine);inst=wt.Instance(store,module,[]);phase='execution';value=inst.exports(store)['run'](store);r=dict(file=file,status='ok',result=value,ms=(time.perf_counter_ns()-start)/1e6)
        except Exception as e:r=dict(file=file,status='error',phase=phase,error=str(e))
        wr.append(r);engine_rows.append(dict(engine='wasmtime',**r))
    dump(out/'wasmtime.json',wr)
    for r in engine_rows:
        if r.get('status')!='ok' or r.get('result')!=expected[r['file']]:errors.append(dict(kind='engine-mismatch',**r))
    summary=dict(cases=len(cases),type_templates=len(typecache),reachable=sum(c['enumeration']['reachable'] for c in cases),enumerated_states=enum_states,binaries=len(files),engine_calls=len(engine_rows),fault_controls=len(controls),modes={mode:dict(collections.Counter(r['status'] for r in rows if r['mode']==mode)) for mode in ['staged','dfs-staged','all-deps','null-patch']},errors=errors)
    dump(out/'summary.json',summary);src=out/'source';src.mkdir()
    for p in [Path(__file__),HERE/'realize.py',HERE/'plan.md',ROOT/'research/gc-witness/witness.py',ROOT/'research/gc-witness/run.cjs',ROOT/'research/gc-witness/run-sm.js',CHECKER]:shutil.copy2(p,src/p.name)
    dump(out/'manifest.json',[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()]);print(json.dumps(summary,indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
