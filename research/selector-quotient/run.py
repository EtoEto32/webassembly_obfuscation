import itertools,json,math,platform,random,re,subprocess,sys
from pathlib import Path
import prototype as p
q=p.q;out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
def compositions(total,n):
    for cuts in itertools.combinations(range(1,total),n-1):
        endpoints=(0,)+cuts+(total,);yield [endpoints[i+1]-endpoints[i] for i in range(n)]
models=[]
for M in (2,4,8,16):
    for n in range(2,min(4,M)+1):
        for freq in compositions(M,n):
            B=[sum(freq[:i]) for i in range(n)]
            symbol=lambda r:next(i for i,b in enumerate(B) if b<=r<b+freq[i])
            for s in range(n):
                for r in range(B[s],B[s]+freq[s]):
                    period=M//math.gcd(freq[s],M);ts=[symbol((freq[s]*v+r-B[s])%M) for v in range(period)]
                    first=next((i for i,t in enumerate(ts) if t!=ts[0]),None)
                    assert first is not None,(M,freq,s,r,ts)
                    models.append(dict(M=M,frequencies=freq,symbol=s,residue=r,period=period,first_value=0,first_next_symbol=ts[0],second_value=first,second_next_symbol=ts[first]))
q.save(out/'selector-model.json',dict(configurations=len(models),value_checks=sum(x['period'] for x in models),fixed_successors=0,rows=models))
fixtures={'identity':[(1,0)],'affine':[(3,5)],'chain3':[(3,5),(5,0x12345678),(7,0xfedcba98)],'chain7':[(1,1),(3,0xffffffff),(0x80000001,7),(5,11),(7,0),(0xfffffffd,0x80000000),(9,0x13579bdf)]}
inputs=[0,1,2,3,7,8,15,16,255,256,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];rng=random.Random(211028);inputs += [rng.getrandbits(32) for _ in range(1024)]
q.save(out/'inputs.json',inputs);q.save(out/'fixtures.json',fixtures);rows=[];recoveries=[]
for name,ops in fixtures.items():
    source=out/(name+'-source.wasm');q.compile(p.source(ops),source)
    for mode in ('plain','decoder','lift'):
        raw=out/(name+'-'+mode+'-raw.wasm')
        if mode=='plain':q.compile(p.source(ops),raw);info={}
        else:info=p.transform(source,raw,mode)
        for opt in ('raw','O3'):
            f=raw if opt=='raw' else out/(name+'-'+mode+'-O3.wasm')
            if opt=='O3':q.tool('wasm-opt',[raw,'-O3','-o',f])
            rows.append(dict(kernel=name,mode=mode,opt=opt,file=f.name,bytes=f.stat().st_size,sha256=q.digest(f),transform=info))
            if mode=='lift':
                dst=f.with_name(f.stem+'-recovered.wasm');rec=p.recover(f,dst);recoveries.append(dict(file=f.name,**rec))
                rows.append(dict(kernel=name,mode='recovered',opt=opt,file=dst.name,bytes=dst.stat().st_size,sha256=q.digest(dst)))
q.save(out/'manifest.json',rows);q.save(out/'recovery.json',recoveries)
subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=60)
interpreter=[]
for row in rows:
    if row['mode']=='decoder':continue
    m=q.read(out/row['file']);index=next(x[2][1] for x in m[1:] if x[:2]==['export','"run"']);nf=len([x for x in m[1:] if x[0]=='func'])
    xs=[0,1,0x80000000,0xffffffff]
    for i,x in enumerate(xs):m.append(['func',['result','i32'],['call',index,['i32.const',str(x)]]]);m.append(['export','"probe'+str(i)+'"',['func',str(nf+i)]])
    dst=out/('interp-'+row['file']);q.compile(q.w.emit(m),dst);log=q.w.tool('wasm-interp',[dst,'--run-all-exports']);(out/(dst.stem+'.log')).write_text(log,encoding='utf-8')
    got={int(i):int(x) for i,x in re.findall(r'probe(\d+)\(\) => i32:(\d+)',log)};want=[]
    for x in xs:
        for a,b in fixtures[row['kernel']]:x=(a*x+b)&p.MASK
        want.append(x)
    assert len(got)==4 and [got[i] for i in range(4)]==want
    interpreter.append(dict(file=row['file'],inputs=xs,outputs=want))
q.save(out/'interpreter.json',dict(calls=len(interpreter)*4,rows=interpreter))
q.save(out/'environment.json',dict(platform=platform.platform(),python=sys.version,node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=q.w.tool('wasm-validate',['--version']).strip(),binaryen=q.tool('wasm-opt',['--version']).strip()))
q.save(out/'sources.json',[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in Path(__file__).parent.iterdir() if f.suffix in ('.py','.cjs','.md')])
print(json.dumps(dict(model_configurations=len(models),model_value_checks=sum(x['period'] for x in models),targets=len(rows),recovered=len(recoveries),interpreter_calls=4*len(interpreter))))
