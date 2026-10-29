"""Replay binaries, check another engine and a logically equivalent non-BCP control."""
import json,random,re,subprocess,sys
from pathlib import Path
import prototype as p
q=p.q;src,runtime,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
read=lambda d,n:json.loads((d/n).read_text(encoding='utf-8'))
rows=read(src,'manifest.json');fixtures=read(src,'fixtures.json');replayed=[];interpreter=[]
for name,f in fixtures.items():
    source=out/(name+'-source.wasm');q.compile(p.source(f['n'],f['ops']),source)
    assert q.digest(source)==q.digest(src/source.name)
    for mode in ('plain','cnf','project'):
        raw=out/(name+'-'+mode+'-raw.wasm')
        if mode=='plain':q.compile(p.source(f['n'],f['ops']),raw)
        else:p.transform(source,raw,mode)
        for opt in ('raw','O3'):
            target=raw if opt=='raw' else out/(name+'-'+mode+'-O3.wasm')
            if opt=='O3':q.tool('wasm-opt',[raw,'--enable-simd','-O3','-o',target])
            p.recover(target,target.with_name(target.stem+'-recovered.wasm'))
for row in rows:
    f=src/row['file'];assert q.digest(f)==row['sha256']==q.digest(out/row['file'])
    q.w.tool('wasm-validate',[f]);replayed.append(dict(file=row['file'],sha256=row['sha256']))
    m=q.read(f);fixture=fixtures[row['kernel']];n=fixture['n'];rng=random.Random(211034);expected=[]
    for case in range(4):
        words=[[0 if case==0 else 0xffffffff if case==1 else ((0xaaaaaaaa^(i*0x01010101)^(j*0x12345678))&0xffffffff) if case==2 else rng.getrandbits(32) for j in range(4)] for i in range(n)]
        body=[]
        for i,vs in enumerate(words):body.append(['v128.store',['i32.const',str(16*i)],['v128.const','i32x4',*map(str,vs)]])
        values=[list(v) for v in words]
        for op,a,b in fixture['ops']:
            values.append([((values[a][i]&values[b][i]) if op=='and' else (values[a][i]|values[b][i]) if op=='or' else (values[a][i]^values[b][i]) if op=='xor' else ~values[a][i])&0xffffffff for i in range(4)])
        expected.append(values[-1][case])
        body.extend([['call','0'],['i32.load',['i32.const',str(16*n+4*case)]]])
        m.append(['func',['result','i32'],*body]);m.append(['export','"probe'+str(case)+'"',['func',str(case+1)]])
    target=out/('interp-'+row['file']);q.compile(q.w.emit(m),target)
    log=q.w.tool('wasm-interp',[target,'--run-all-exports']);target.with_suffix('.log').write_text(log,encoding='utf-8')
    got={int(i):int(x) for i,x in re.findall(r'probe(\d+)\(\) => i32:(\d+)',log)}
    assert [got[i] for i in range(4)]==expected
    interpreter.append(dict(file=row['file'],outputs=expected))
# Equivalent clauses C == (C or u) and (C or not u) need resolution, not only UP.
f=fixtures['parity8'];n=f['n'];output=n+len(f['ops']);cs,_=p.eliminate(p.cnf(n,f['ops']),n,output);u=output+1
stalled=p.normalize([list(c)+[s*u] for c in cs for s in (-1,1)])
wat,info=p.generate(n,stalled,output);negative=out/'equivalent-stalled-raw.wasm';q.compile(wat,negative)
negatives=[]
for opt in ('raw','O3'):
    file=negative if opt=='raw' else out/'equivalent-stalled-O3.wasm'
    if opt=='O3':q.tool('wasm-opt',[negative,'--enable-simd','-O3','-o',file])
    script="const fs=require('fs');const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;const before=Buffer.from(new Uint8Array(e.memory.buffer));let result;try{e.run();result={status:'returned'};}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;result={status:'diagnostic-trap',message:String(err)};}result.memory_unchanged=before.equals(Buffer.from(e.memory.buffer));console.log(JSON.stringify(result));"
    r=json.loads(subprocess.check_output(['node','-e',script,str(file)],text=True,timeout=30));assert r['status']=='diagnostic-trap' and r['memory_unchanged']
    negatives.append(dict(file=file.name,input='all zero vectors',original_output='all zero',cnf_relation='logically equivalent after adding unused variable u, but unit propagation incomplete',**r))
# Valid Wasm outside the exact accepted source profile must be rejected.
rejections=[]
for name in ('extra-export','mutable-arity','extra-store'):
    m=q.read(src/'parity8-source.wasm')
    if name=='extra-export':m.append(['export','"other"',['func','0']])
    elif name=='mutable-arity':next(x for x in m[1:] if x[0]=='global')[1]=['mut','i32']
    else:next(x for x in m[1:] if x[0]=='func').append(['i32.store',['i32.const','4096'],['i32.const','7']])
    file=out/(name+'.wasm');q.compile(q.w.emit(m),file)
    try:p.parse(file)
    except p.Unsupported as e:rejections.append(dict(file=file.name,status='unsupported',reason=str(e)))
    else:raise AssertionError('accepted '+name)
checks=read(src,'checks.json');assert checks['targets']==48 and checks['calls']==19176
assert all(r['mismatches']==r['unexpected_traps']==0 for r in checks['records'])
assert len(read(src,'recovery.json'))==24
canonical=[]
for name in fixtures:
    recovered=[r for r in rows if r['kernel']==name and r['mode'].endswith('-recovered')]
    assert len(recovered)==6 and len({r['sha256'] for r in recovered})==1
    canonical.append(dict(kernel=name,conditions=6,sha256=recovered[0]['sha256']))
assert read(runtime,'checks.json')['calls']==6392
assert len(read(runtime,'runtime.json'))==80 and len(read(runtime,'summary.json'))==16
for d in (src,runtime):
    for r in read(d,'sources.json'):assert q.digest(p.ROOT/r['file'])==r['sha256'],r['file']
sources=sorted(Path(__file__).parent.glob('*.py'))+sorted(Path(__file__).parent.glob('*.cjs'))+[p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']
tool_files=[p.ROOT/'.tools/wabt-1.0.42/bin'/n for n in ('wat2wasm.exe','wasm2wat.exe','wasm-validate.exe','wasm-interp.exe')]+[p.ROOT/'.tools/binaryen-version_133/bin/wasm-opt.exe']
evidence=[dict(file=str(f.resolve().relative_to(p.ROOT)),sha256=q.digest(f)) for d in (src,runtime) for f in sorted(d.iterdir()) if f.suffix in ('.json','.wasm')]
q.save(out/'audit.json',dict(main_calls=19176,benchmark_recheck_calls=6392,replay=replayed,wabt_calls=4*len(interpreter),interpreter=interpreter,canonical_recovered=canonical,negative_controls=negatives,rejections=rejections,sources=[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in sources],tools=[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in tool_files],evidence=evidence))
print(json.dumps(dict(rebuilt=len(replayed),wabt_calls=4*len(interpreter),canonical_groups=len(canonical),negative_controls=len(negatives),rejections=len(rejections))))
