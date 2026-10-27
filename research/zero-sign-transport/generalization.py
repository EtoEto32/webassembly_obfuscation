"""Post-main protocol: shared DAGs, arity coverage and rounding counterexamples."""
import json, random, re, subprocess, sys
from pathlib import Path
import prototype as p
import model
q=p.q
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
edge=[0,0x80000000,1,0x80000001,0x007fffff,0x00800000,0x3f000000,0x3f800000,0xbf800000,0x3f800001,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00000,0x7f800001]
summaries=[]
for case,(n,count) in enumerate(zip((1,2,3,5,9,16),(4,8,16,24,32,48))):
    rng=random.Random(211027+case);nodes=[('input',i) for i in range(n)];root=0
    for _ in range(count):
        a,b=root,rng.randrange(len(nodes))
        if rng.randrange(2):a,b=b,a
        nodes.append((rng.choice(('add','sub','mul')),a,b));root=len(nodes)-1
    inputs=[[x]*n for x in edge]
    for i in range(n):
        for x in edge:
            row=[0x3f800000]*n;row[i]=x;inputs.append(row)
    inputs += [[rng.getrandbits(32) for _ in range(n)] for _ in range(1024)]
    inputs += [[rng.choice((0,0x80000000,rng.getrandbits(32))) for _ in range(n)] for _ in range(128)]
    folder=out/f'arity-{n}';folder.mkdir();name=f'arity-{n}'
    q.save(folder/'inputs.json',inputs)
    q.save(folder/'fixtures.json',{name:dict(nodes=nodes,root=root,expected=[model.evaluate(nodes,root,x) for x in inputs])})
    source=folder/'source.wasm';q.compile(p.generate(n,nodes,root,'plain',0)[0],source)
    rows=[];attacks=[]
    for mode in ('plain','eager','deferred'):
        for seed in ((0,) if mode=='plain' else (17,109)):
            raw=folder/f'{mode}-{seed}-raw.wasm';info=p.transform(source,raw,mode,seed)
            for opt in ('raw','O3'):
                target=raw if opt=='raw' else folder/f'{mode}-{seed}-O3.wasm'
                if opt=='O3':q.tool('wasm-opt',[raw,'-O3','-o',target])
                rows.append(dict(kernel=name,mode=mode,seed=seed,opt=opt,file=target.name,sha256=q.digest(target),transform=info))
                if mode=='deferred':
                    candidate=target.with_name(target.stem+'-candidate.wasm')
                    try:
                        rec=p.recover(target,candidate)
                        residual=target.with_name(target.stem+'-residual.wasm');p.residual_recovery(target,candidate,residual)
                        for m,f in (('candidate',candidate),('residual',residual)):
                            rows.append(dict(kernel=name,mode=m,seed=seed,opt=opt,file=f.name,sha256=q.digest(f)))
                        attacks.append(dict(file=target.name,status='candidate-extracted',**rec))
                    except p.Unsupported as e:attacks.append(dict(file=target.name,status='unsupported',reason=str(e)))
    q.save(folder/'manifest.json',rows);q.save(folder/'attacks.json',attacks)
    subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(folder),'--positive-only'],check=True,timeout=60)
    checks=json.loads((folder/'checks.json').read_text())
    summaries.append(dict(arity=n,source_arithmetic_nodes=count,inputs=len(inputs),targets=len(rows),calls=checks['calls'],positive_calls=sum(x['mode'] not in ('candidate','uncorrected') for x in rows)*len(inputs),positive_mismatches=checks['positive_mismatches'],candidate_failures=sum(x['mode']=='candidate' and x['mismatches']>0 for x in checks['records']),candidate_mismatches=sum(x['mismatches'] for x in checks['records'] if x['mode']=='candidate'),attacks=attacks))
    q.save(out/'generalization.json',summaries);print(name,flush=True)

# These mutants deliberately change rounding; they are not protected variants.
triples={'fused-rounding':[0x3f800001,0x3f7ffffe,0xbf800000],'reassociation':[0x4b800000,0x3f800000,0xcb800000]}
def literal(x):return f'(f32.reinterpret_i32 (i32.const {x}))'
controls=[]
for name,xs in triples.items():
    a,b,c=map(literal,xs)
    if name=='fused-rounding':
        original=f'(f32.add (f32.mul {a} {b}) {c})'
        changed=f'(f32.demote_f64 (f64.add (f64.mul (f64.promote_f32 {a}) (f64.promote_f32 {b})) (f64.promote_f32 {c})))'
        expected=model.operation('add',model.operation('mul',xs[0],xs[1]),xs[2])
    else:
        original=f'(f32.add (f32.add {a} {b}) {c})';changed=f'(f32.add {a} (f32.add {b} {c}))'
        expected=model.operation('add',model.operation('add',xs[0],xs[1]),xs[2])
    wat=f'(module (func (export "original") (result i32) (i32.reinterpret_f32 {original})) (func (export "changed") (result i32) (i32.reinterpret_f32 {changed})))'
    raw=out/(name+'-raw.wasm');q.compile(wat,raw)
    for opt in ('raw','O3'):
        f=raw if opt=='raw' else out/(name+'-O3.wasm')
        if opt=='O3':q.tool('wasm-opt',[raw,'-O3','-o',f])
        log=q.w.tool('wasm-interp',[f,'--run-all-exports']);(out/(f.stem+'.log')).write_text(log,encoding='utf-8')
        got={k:int(v) for k,v in re.findall(r'(original|changed)\(\) => i32:(\d+)',log)}
        node=json.loads(subprocess.check_output(['node','-e',"const e=new WebAssembly.Instance(new WebAssembly.Module(require('fs').readFileSync(process.argv[1]))).exports; console.log(JSON.stringify({original:e.original()>>>0,changed:e.changed()>>>0}))",str(f)],text=True))
        assert got==node and got['original']==expected and got['changed']!=expected
        controls.append(dict(name=name,opt=opt,input=xs,expected=expected,interpreter=got,node=node,sha256=q.digest(f)))
q.save(out/'rounding-controls.json',controls)
q.save(out/'sources.json',[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in Path(__file__).parent.iterdir() if f.suffix in ('.py','.cjs')])
print(json.dumps(dict(cases=len(summaries),targets=sum(x['targets'] for x in summaries),calls=sum(x['calls'] for x in summaries),positive_calls=sum(x['positive_calls'] for x in summaries),candidate_failures=sum(x['candidate_failures'] for x in summaries),rounding_controls=len(controls))))
