import json,platform,random,subprocess,sys
from pathlib import Path
import prototype as p
q=p.q;out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
fixtures={}
def build(name,n,kind):
    ops=[]
    def gate(op,a,b=0):ops.append((op,a,b));return n+len(ops)-1
    if kind=='parity':
        v=0
        for i in range(1,n):v=gate('xor',v,i)
    elif kind=='mux':
        def mux(s,a,b):return gate('or',gate('and',s,a),gate('and',gate('not',s),b))
        leaves=[3,4,5,6,7,8,3,6]
        for s in range(3):leaves=[mux(s,a,b) for a,b in zip(leaves[::2],leaves[1::2])]
    elif kind=='carry':
        c=gate('and',0,1)
        for i in range(2,n,2):c=gate('or',gate('and',i,i+1),gate('and',gate('xor',i,i+1),c))
    else:
        a,b=0,1
        for i in range(2,n):
            a=gate('xor',a,gate('and',b,i));b=gate('xor',b,gate('or',a,i))
        gate('xor',a,b)
    fixtures[name]=dict(n=n,ops=ops)
build('parity8',8,'parity');build('mux9',9,'mux');build('carry12',12,'carry');build('shared16',16,'shared')
q.save(out/'fixtures.json',fixtures);rows=[];recovery=[];models=[]
def propagate(cs,known,limit):
    values=dict(known)
    for turn in range(limit+1):
        old=dict(values)
        for c in cs:
            if any(values.get(abs(l))==(l>0) for l in c):continue
            missing=[l for l in c if abs(l) not in values]
            if not missing:return None
            if len(missing)==1:values[abs(missing[0])]=missing[0]>0
        if values==old:return values
    raise AssertionError('propagation did not reach fixed point')
for name,f in fixtures.items():
    n,ops=f['n'],f['ops'];source=out/(name+'-source.wasm');q.compile(p.source(n,ops),source)
    cs=p.cnf(n,ops);projected,log=p.eliminate(cs,n,n+len(ops));remaining={abs(l) for c in projected for l in c}
    rng=random.Random(211030+n);probes=[]
    for trial in range(256):
        known={i:bool(rng.getrandbits(1)) for i in range(1,n+1) if rng.randrange(3)!=0}
        a=propagate(cs,known,n+len(ops));b=propagate(projected,known,n+len(ops))
        assert a is not None and b is not None
        assert {i:v for i,v in a.items() if i in remaining}.items()<=b.items()
        probes.append(dict(input=known,before=len(a),after=len(b)))
    models.append(dict(kernel=name,initial_clauses=len(cs),final_clauses=len(projected),eliminations=log,partial_assignments=probes))
    for mode in ('plain','cnf','project'):
        raw=out/(name+'-'+mode+'-raw.wasm')
        if mode=='plain':q.compile(p.source(n,ops),raw);info={}
        else:info=p.transform(source,raw,mode)
        for opt in ('raw','O3'):
            f=raw if opt=='raw' else out/(name+'-'+mode+'-O3.wasm')
            if opt=='O3':q.tool('wasm-opt',[raw,'--enable-simd','-O3','-o',f])
            rows.append(dict(kernel=name,mode=mode,opt=opt,file=f.name,bytes=f.stat().st_size,sha256=q.digest(f),transform=info))
            target=f.with_name(f.stem+'-recovered.wasm');rec=p.recover(f,target);recovery.append(dict(file=f.name,**rec))
            rows.append(dict(kernel=name,mode=mode+'-recovered',opt=opt,file=target.name,bytes=target.stat().st_size,sha256=q.digest(target)))
q.save(out/'manifest.json',rows);q.save(out/'recovery.json',recovery);q.save(out/'model.json',models)
subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=120)
q.save(out/'environment.json',dict(platform=platform.platform(),python=sys.version,node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=q.w.tool('wasm-validate',['--version']).strip(),binaryen=q.tool('wasm-opt',['--version']).strip()))
q.save(out/'sources.json',[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in Path(__file__).parent.iterdir() if f.suffix in ('.py','.md','.cjs')])
print(json.dumps(dict(targets=len(rows),recoveries=len(recovery),models=[dict(kernel=r['kernel'],before=r['initial_clauses'],after=r['final_clauses'],eliminated=len(r['eliminations'])) for r in models])))
