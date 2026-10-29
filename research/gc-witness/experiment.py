import argparse,collections,hashlib,importlib.metadata,json,platform,random,shutil,subprocess,sys,time
from pathlib import Path
from witness import ROOT,CHECKER,read,generate,closure,memo_order,Unsupported,Empty,Budget,type_text
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.tools/import-alias-quotient-python'));import wasmtime as wt
def dump(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(i,nullable=False):return dict(ref=dict(index=i),nullable=nullable)
def field(v):return dict(value=v,mutable=False)
def struct(*vs):return dict(kind='struct',fields=list(map(field,vs)))
def array(v):return dict(kind='array',fields=[field(v)])
def model(ts):return dict(types=ts,groups=[dict(start=0,length=len(ts))])
def fixtures():
    rows=[]
    def add(name,ts,tasks):rows.append(dict(name=name,model=model(ts),tasks=tasks))
    add('self-struct',[struct(ref(0))],[(0,[],False)])
    add('mutual-struct',[struct(ref(1)),struct(ref(0))],[(0,[],False),(1,[],False)])
    add('nullable-cycle',[struct(ref(1)),struct(ref(0,True))],[(0,[],True),(0,[0,0],True)])
    add('self-array',[array(ref(0))],[(0,[],True),(0,['e'],True),(0,['e']*12,True)])
    add('array-breaks-cycle',[struct(ref(1)),array(ref(0))],[(0,[],True),(0,[0,'e',0,'e'],True),(1,['e'],True)])
    add('empty-element',[struct(ref(0)),array(ref(0))],[(0,[],False),(1,[],True),(1,['e'],False)])
    add('function-breaks-cycle',[struct(ref(1)),dict(kind='func',params=[],results=[ref(0)])],[(0,[],True),(0,[0],True)])
    for width in [1,2,4]:
        for n in [2,5,9,13,21]:
            ts=[struct(dict(scalar='i32'))]+[struct(*[ref(i-1)]*width) for i in range(1,n)]
            add('chain-%d-%d'%(width,n),ts,[(n-1,[],True),(n-1,[0]*(n-1),True)])
    rng=random.Random(20261026)
    for seed in range(64):
        n=rng.randrange(2,9);ts=[]
        for i in range(n):
            kind=rng.choice(['struct','struct','array','func'])
            vals=[ref(rng.randrange(n),rng.random()<.2) for _ in range(rng.randrange(0,4))]
            if kind=='struct':ts.append(struct(*vals))
            elif kind=='array':ts.append(array(ref(rng.randrange(n),rng.random()<.2)))
            else:ts.append(dict(kind='func',params=[ref(rng.randrange(n))],results=[ref(rng.randrange(n))]))
        add('random-%02d'%seed,ts,[(i,[],None) for i in range(n)])
    return rows

def enumerated_reachability(types):
    """Enumerate all sets of created type witnesses, independently of dependency code."""
    states={0};frontier=[0];seen=0
    while frontier:
        state=frontier.pop();seen|=state
        for i,t in enumerate(types):
            if state>>i&1:continue
            possible=True
            if t['kind']=='struct':
                for f in t['fields']:
                    v=f['value']
                    if 'ref' in v and not v['nullable'] and not (state>>v['ref']['index']&1):possible=False;break
            if possible:
                nxt=state|(1<<i)
                if nxt not in states:states.add(nxt);frontier.append(nxt)
    return [i for i in range(len(types)) if seen>>i&1],len(states)

def main(out):
    out.mkdir(parents=True,exist_ok=False);src=out/'source';src.mkdir()
    for p in [*HERE.glob('*.py'),*HERE.glob('*.cjs'),*HERE.glob('*.js'),*HERE.glob('checker/src/*.rs'),HERE/'checker/Cargo.toml',HERE/'checker/Cargo.lock',CHECKER]:shutil.copy2(p,src/p.name)
    rows=[];models=[];files=[];errors=[];enums=[];timing=[];build=[]
    for fx in fixtures():
        name=fx['name'];m=fx['model'];wat='(module\n'+type_text(m)+')';p=out/(name+'-types.wasm');p.write_bytes(wt.wat2wasm(wat));(out/(name+'-types.wat')).write_text(wat)
        parsed=read(p)
        if parsed['types']!=m['types']:errors.append(dict(kind='parse',name=name))
        live=set(closure(parsed['types']));memo=set(memo_order(parsed['types']));old=set(closure(parsed['types'],True))
        if memo!=live:errors.append(dict(kind='memo-disagrees',name=name))
        if len(m['types'])<=8:
            reach,count=enumerated_reachability(m['types']);enums.append(dict(name=name,states=count,inhabited=reach))
            if set(reach)!=live:errors.append(dict(kind='enumeration-disagrees',name=name))
        models.append(dict(name=name,file=p.name,model=parsed,inhabited=sorted(live),conservative_inhabited=sorted(old)))
        for task,(target,path,expected) in enumerate(fx['tasks']):
            for mode in ['tree','memo','worklist']:
                record=dict(name=name,task=task,target=target,path=path,mode=mode,expected=expected,conservative_root=target in old)
                try:
                    g=generate(parsed,target,path,mode,node_budget=2048,depth_budget=64)
                    bname='%s-%d-%s'%(name,task,mode);f=out/(bname+'.wasm');(out/(bname+'.wat')).write_text(g['wat']);t=time.perf_counter_ns();f.write_bytes(wt.wat2wasm(g.pop('wat')))
                    # Validate the real output with the same independent Rust validator.
                    read(f)
                    build.append(dict(file=f.name,ms=(time.perf_counter_ns()-t)/1e6,bytes=f.stat().st_size))
                    record.update(status='generated',file=f.name,**g);files.append(f.name)
                    if expected is False:errors.append(dict(kind='unexpected-construction',**record))
                except (Unsupported,Empty,Budget) as e:
                    record.update(status=type(e).__name__,reason=str(e))
                    if expected is True and mode!='tree':errors.append(dict(kind='missed-known-witness',**record))
                rows.append(record)
    dump(out/'models.json',models);dump(out/'generation.json',rows);dump(out/'enumeration.json',enums);dump(out/'build.json',build)
    request=dict(directory=str(out.resolve()),files=files);dump(out/'request.json',request)
    engine_rows=[]
    for engine,cmd in [('node',['node',str(HERE/'run.cjs'),str(out/'request.json')]),('spidermonkey',[str(ROOT/'.tools/spidermonkey-150.0.1/js.exe'),'--wasm-compiler=baseline+ion',str(HERE/'run-sm.js'),str(out/'request.json')])]:
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=90);dump(out/(engine+'-process.json'),dict(code=cp.returncode,stderr=cp.stderr))
        if cp.returncode!=0:errors.append(dict(kind='engine-process',engine=engine));continue
        obj=json.loads(cp.stdout);dump(out/(engine+'.json'),obj)
        engine_rows.extend([dict(engine=engine,**r) for r in obj['rows']])
    cfg=wt.Config();engine=wt.Engine(cfg);wrows=[]
    for file in files:
        store=wt.Store(engine);t=time.perf_counter_ns()
        try:
            m=wt.Module(engine,(out/file).read_bytes());inst=wt.Instance(store,m,[]);result=inst.exports(store)['run'](store)
            wrows.append(dict(file=file,status='ok',result=result,ms=(time.perf_counter_ns()-t)/1e6))
        except Exception as e:wrows.append(dict(file=file,status='error',reason=str(e)))
    dump(out/'wasmtime.json',dict(version=importlib.metadata.version('wasmtime'),rows=wrows));engine_rows.extend([dict(engine='wasmtime',**r) for r in wrows])
    for r in engine_rows:
        if r['status']!='ok' or r.get('result')!=1:errors.append(dict(kind='execution',**r))
    summary=dict(models=len(models),types=sum(len(m['model']['types']) for m in models),inhabited=sum(len(m['inhabited']) for m in models),conservative_inhabited=sum(len(m['conservative_inhabited']) for m in models),
        generation=dict(collections.Counter(r['status'] for r in rows)),by_mode={mode:dict(collections.Counter(r['status'] for r in rows if r['mode']==mode)) for mode in ['tree','memo','worklist']},
        generated_binaries=len(files),executions=len(engine_rows),engine_status=dict(collections.Counter(r['engine']+':'+r['status'] for r in engine_rows)),enumerated_models=len(enums),enumerated_states=sum(r['states'] for r in enums),errors=errors)
    dump(out/'summary.json',summary);dump(out/'environment.json',dict(python=sys.version,platform=platform.platform(),cpu=platform.processor(),wasmtime=importlib.metadata.version('wasmtime'),seed=20261026,budget_nodes=2048,budget_depth=64))
    records=[dict(path=str(p.resolve()),sha256=digest(p)) for p in out.rglob('*') if p.is_file()];dump(out/'manifest.json',records)
    print(json.dumps(summary,indent=2));assert not errors
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);main(ap.parse_args().out)
