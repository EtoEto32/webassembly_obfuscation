import itertools,json,random,subprocess,sys,time
from pathlib import Path
import prototype as p
import model
q=p.q;out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
def fixture(name):
    nodes=[('input',i) for i in range(3)]
    def op(tag,a,b):nodes.append((tag,a,b));return len(nodes)-1
    if name=='fma':root=op('add',op('mul',0,1),2)
    if name=='horner12':
        root=2
        for i in range(12):root=op('sub' if i%3==1 else 'add',op('mul',root,0),1)
    if name=='rotation8':
        a,b=0,1
        for i in range(8):a,b=op('sub',op('mul',a,2),op('mul',b,1)),op('add',op('mul',a,1),op('mul',b,2))
        root=op('add',a,b)
    if name=='zero-control':root=op('add',op('mul',op('sub',0,0),1),op('sub',2,2))
    return nodes,root
edge=[0,0x80000000,1,0x80000001,0x007fffff,0x00800000,0x3f000000,0x3f800000,0xbf800000,0x3f800001,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00000,0x7f800001]
inputs=[list(x) for x in itertools.product(edge,repeat=3)];rng=random.Random(211026)
inputs += [[rng.getrandbits(32) for _ in range(3)] for _ in range(2048)]
inputs += [[rng.choice([0,0x80000000,rng.getrandbits(32)]) for _ in range(3)] for _ in range(512)]
q.save(out/'inputs.json',inputs);fixtures={};rows=[];attacks=[]
for name in ('fma','horner12','rotation8','zero-control'):
    nodes,root=fixture(name);fixtures[name]=dict(nodes=nodes,root=root,expected=[model.evaluate(nodes,root,x) for x in inputs])
    source=out/(name+'-source.wasm');q.compile(p.generate(3,nodes,root,'plain',0)[0],source)
    for mode in ('plain','eager','deferred','uncorrected'):
        for seed in ([0] if mode=='plain' else [37,91]):
            dst=out/f'{name}-{mode}-{seed}-raw.wasm';info=p.transform(source,dst,mode,seed)
            for opt in ('raw','O3'):
                target=dst if opt=='raw' else out/f'{name}-{mode}-{seed}-O3.wasm'
                if opt=='O3':q.tool('wasm-opt',[dst,'-O3','-o',target])
                row=dict(kernel=name,mode=mode,seed=seed,opt=opt,file=target.name,bytes=target.stat().st_size,sha256=q.digest(target),transform=info)
                rows.append(row)
                if mode=='deferred':
                    recovered=target.with_name(target.stem+'-recovered.wasm')
                    try:
                        attack=p.recover(target,recovered)
                        rows.append(dict(kernel=name,mode='candidate',seed=seed,opt=opt,file=recovered.name,bytes=recovered.stat().st_size,sha256=q.digest(recovered)))
                        residual=target.with_name(target.stem+'-residual.wasm');p.residual_recovery(target,recovered,residual)
                        rows.append(dict(kernel=name,mode='residual',seed=seed,opt=opt,file=residual.name,bytes=residual.stat().st_size,sha256=q.digest(residual)))
                        attacks.append(dict(file=target.name,status='candidate-extracted',recovered=recovered.name,residual=residual.name,**attack))
                    except p.Unsupported as e:attacks.append(dict(file=target.name,status='unsupported',reason=str(e)))
    print(name,flush=True)
q.save(out/'fixtures.json',fixtures);q.save(out/'manifest.json',rows);q.save(out/'attacks.json',attacks)
subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=60)
print(json.dumps(dict(targets=len(rows),inputs=len(inputs),attacks=len(attacks))))
