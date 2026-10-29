import json,random,subprocess,sys,time
from pathlib import Path
import prototype as p
q=p.q;m=p.m
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);rows=[];fixtures=[]
for name,(n,ops) in m.FIXTURES.items():
    data=bytes(random.Random(211042+i).randrange(256) for i in range(n));src=out/(name+'-source.wasm');q.compile(p.wat(data,ops),src)
    fixtures.append(dict(name=name,n=n,data=list(data),copies=ops))
    for mode in ('plain','uniform','conjugate','native'):
        f=out/(name+'-'+mode+'-raw.wasm')
        if mode=='plain':q.compile(p.wat(data,ops),f);info=dict(n=n,copies=ops,matrix=m.ident(n),inverse=m.ident(n),elapsed_ms=0)
        else:info=p.transform(src,f,mode)
        for opt in ('raw','O3'):
            dst=f if opt=='raw' else out/(name+'-'+mode+'-O3.wasm')
            if opt=='O3':q.tool('wasm-opt',[f,'--enable-bulk-memory','-O3','-o',dst])
            obs=out/(dst.stem+'-observed.wasm');p.probe(dst,obs)
            rows.append({**info,**dict(kernel=name,mode=mode,opt=opt,file=dst.name,observed=obs.name,bytes=dst.stat().st_size,sha256=q.digest(dst))})
q.save(out/'fixtures.json',fixtures);q.save(out/'manifest.json',rows)
subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=120)
q.save(out/'sources.json',[dict(file=str(f.relative_to(p.ROOT)),sha256=q.digest(f)) for f in Path(__file__).parent.iterdir() if f.suffix in ('.py','.cjs','.md')])
print(json.dumps(dict(targets=len(rows),dimensions={k:m.choose(n,ops)[1]['dimension'] for k,(n,ops) in m.FIXTURES.items()})))
