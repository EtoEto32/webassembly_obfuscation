import json,random,re,subprocess,sys
from pathlib import Path
import prototype as p
q=p.q;m=p.m
src,recovery,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
rows=json.loads((src/'manifest.json').read_text());fixtures={f['name']:f for f in json.loads((src/'fixtures.json').read_text())}
model_checks=[];rng=random.Random(211046)
for n in (2,3):
    possible=[(d,s,l) for l in range(1,n+1) for d in range(n-l+1) for s in range(n-l+1) if d!=s]
    for t in range(14):
        ops=[] if t==0 else possible if t==1 else [op for op in possible if rng.randrange(2)]
        basis=m.centralizer(n,ops);span={0}
        for b in basis:span|={x^b for x in list(span)}
        brute=set()
        for v in range(1<<(n*n)):
            a=[(v>>(i*n))&((1<<n)-1) for i in range(n)]
            if all(m.product(a,m.matrix(n,op))==m.product(m.matrix(n,op),a) for op in ops):brute.add(v)
        assert brute==span
        model_checks.append(dict(n=n,ops=ops,dimension=len(basis),enumerated=1<<(n*n),solutions=len(span)))

regenerated=[];engines=[]
for row in rows:
    f=fixtures[row['kernel']];data=bytes(f['data']);b,info=m.choose(f['n'],f['copies']);raw=out/(row['kernel']+'-'+row['mode']+'-raw.wasm')
    if not raw.exists():q.compile(p.wat(data,f['copies'],b,row['mode']),raw)
    dst=raw
    if row['opt']=='O3':dst=out/row['file'];q.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',dst])
    assert q.digest(dst)==row['sha256'];regenerated.append(dict(file=row['file'],sha256=q.digest(dst)))

allrows=[(src,row) for row in rows]+[(recovery,row) for row in json.loads((recovery/'manifest.json').read_text())]
for folder,row in allrows:
    module=q.read(folder/row['file']);fs=[x for x in module[1:] if x[0]=='func'];exports={x[1][1:-1]:int(x[2][1]) for x in module[1:] if x[0]=='export' and x[2][0]=='func'}
    f=fixtures[row['kernel']];ref=bytearray(f['data']);ref[0]=133;ref[-1]=201
    calls=[f'(call {exports["write"]} (i32.const 0) (i32.const 133))',f'(call {exports["write"]} (i32.const {len(ref)-1}) (i32.const 201))']
    for j,op in enumerate(f['copies']):
        if j%3==0:
            d,s,l=op;ref[d:d+l]=bytes(ref[s:s+l]);calls.append(f'(call {exports["copy"+str(j)]})')
    want=0;expr='(i32.const 0)'
    for i,x in enumerate(ref):want=((want*16777619)^x)&0xffffffff;expr=f'(i32.xor (i32.mul {expr} (i32.const 16777619)) (call {exports["read"]} (i32.const {i})))'
    module=[module[0]]+[x for x in module[1:] if x[0]!='export'];module.append(q.w.parse('(module (func (result i32) '+' '.join(calls)+' '+expr+'))')[1]);module.append(['export','"probe"',['func',str(len(fs))]])
    dst=out/('engine-'+row['file']);q.compile(q.w.emit(module),dst)
    text=q.w.tool('wasm-interp',[dst,'--run-all-exports']);match=re.search(r'probe\(\) => i32:(\d+)',text)
    if not match or int(match.group(1))!=want:raise AssertionError(text)
    code='const fs=require("fs");const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;console.log(e.probe()>>>0);'
    got=int(subprocess.check_output(['node','-e',code,str(dst)],text=True));assert got==want
    engines.append(dict(file=row['file'],expected=want,wabt=int(match.group(1)),node=got))

# A missing source operation must produce an actual counterexample, not only a failed matrix test.
n,ops=m.FIXTURES['irregular8'];bad=None
for seed in range(64):
    b,_=m.choose(n,ops[:-1],seed);c=m.matrix(n,ops[-1]);diff=[a^d for a,d in zip(m.product(b,c),m.product(c,b))]
    if any(diff):bad=b;column=next(m.bits(next(x for x in diff if x)));break
assert bad is not None
data=bytes(1 if i==column else 0 for i in range(n));negatives=[]
for kind in ('missing-copy','wrong-write'):
    if kind=='missing-copy':b=bad;initial=data;operation='e.copy'+str(len(ops)-1)+'();';expected=list(initial);d,s,l=ops[-1];expected[d:d+l]=list(initial[s:s+l]);text=p.wat(initial,ops,b,'native')
    else:
        b,_=m.choose(n,ops);initial=bytes(range(1,n+1));expected=list(initial);operation='e.write(0,1);';text=p.wat(initial,ops,b,'native');old=f'(local.set 2 (i32.xor (local.get 1) {p.linear(m.inverse(b)[0])}))';assert old in text;text=text.replace(old,'(local.set 2 (local.get 1))',1)
    for opt in ('raw','O3'):
        raw=out/(kind+'-raw.wasm')
        if not raw.exists():q.compile(text,raw)
        dst=raw if opt=='raw' else out/(kind+'-O3.wasm')
        if opt=='O3':q.tool('wasm-opt',[raw,'--enable-bulk-memory','-O3','-o',dst])
        code='const fs=require("fs");const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;'+operation+'console.log(JSON.stringify(Array.from({length:'+str(n)+'},(_,i)=>e.read(i))));'
        got=json.loads(subprocess.check_output(['node','-e',code,str(dst)],text=True));assert got!=expected;negatives.append(dict(kind=kind,opt=opt,expected=expected,actual=got))

base=p.wat(bytes(range(8)),[(4,0,4)]);rejections=[]
for name,text in [('memory-export',base.replace('(memory 1 1)','(memory (export "memory") 1 1)')),('extra-export',base[:-1]+' (export "alias" (func 0)))'),('copy-outside-window',p.wat(bytes(range(8)),[(7,0,4)]))]:
    f=out/(name+'.wasm');q.compile(text,f)
    try:p.parse(f)
    except ValueError as e:rejections.append(dict(case=name,reason=str(e)))
    else:raise AssertionError('expected rejection '+name)

tools={name:q.w.tool(name,['--version']).strip() for name in ('wat2wasm','wasm-validate','wasm2wat','wasm-interp')};tools['wasm-opt']=q.tool('wasm-opt',['--version']).strip()
pins=[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for folder in (Path(__file__).parent,src,recovery) for f in folder.iterdir() if f.is_file() and f.suffix in ('.py','.cjs','.md','.json','.wasm')]
q.save(out/'audit.json',dict(model_checks=model_checks,regenerated=regenerated,engine_checks=engines,negative_controls=negatives,rejections=rejections,tools=tools,pins=pins))
print(json.dumps(dict(model_systems=len(model_checks),model_matrices=sum(x['enumerated'] for x in model_checks),regenerated=len(regenerated),engine_probes=len(engines),negative_controls=len(negatives),rejections=len(rejections),pinned_files=len(pins))))
