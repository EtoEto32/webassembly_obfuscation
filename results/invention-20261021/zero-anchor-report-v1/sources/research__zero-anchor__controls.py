import json, random, subprocess, sys
from pathlib import Path
import prototype as p

def relaxed(t,i,projection):
    if i<16:return t[i]
    if i>=128 or projection=='zero':return 0
    return t[i%16]

def main(src,out):
    src=Path(src);out=Path(out);out.mkdir(parents=True,exist_ok=False);rng=random.Random(331021);q=p.q
    checks=0;counter=[]
    for op,anchor in [('add',0),('sub',15)]:
        for _ in range(128):
            t=p.permutation(rng,anchor)
            for x in range(16):
                for b in range(2):
                    idx=(x+b if op=='add' else x-b)&255
                    expected=t[idx&15]
                    for projection in ('zero','low-index'):
                        assert relaxed(t,idx,projection)==expected;checks+=1
        # The excluded b=2 case necessarily needs two distinct residues to
        # map to zero. No permutation can satisfy this requirement.
        t=list(range(16));t[anchor],t[0]=t[0],t[anchor]
        for b in (1,2):
            required=sorted({((x+b if op=='add' else x-b)&15) for x in range(16) if not 0<=(x+b if op=='add' else x-b)<16})
            counter.append(dict(op=op,max_step=b,required_zero_residues=required,permutation_feasible=len(required)<=1))
    q.save(out/'algebra.json',dict(byte_projection_checks=checks,limits=counter,scope='two specification projections, not execution on a second engine'))
    # Actual deterministic-profile clones of all candidate binaries, including O3.
    rows=[]
    for r in json.loads((src/'manifest.json').read_text()):
        if r['mode']!='anchor-free':continue
        m=q.read(src/r['file']);changed=0
        for e in q.walk(m):
            if e[0]=='i8x16.relaxed_swizzle':e[0]='i8x16.swizzle';changed+=1
        q.compile(q.w.emit(m),out/r['file']);rows.append(dict(r,changed_to_strict=changed,sha256=q.digest(out/r['file'])))
    q.save(out/'manifest.json',rows);q.save(out/'models.json',json.loads((src/'models.json').read_text()))
    subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],check=True,timeout=120)
    # Actual wrong-anchor control. Relaxed x86 may hide the bug; strict must expose it.
    t=[(i+1)&15 for i in range(16)]
    index=['i8x16.add',q.masked(p.splat(0)),['v128.and',p.splat(1),q.vc([1]*16)]]
    vals={}
    for variant in ('masked','relaxed-unmasked','strict-unmasked'):
        e=p.sw(t,q.masked(index) if variant=='masked' else index)
        if variant=='strict-unmasked':e[0]='i8x16.swizzle'
        dst=out/(variant+'.wasm');q.compile(p.module(e),dst)
        code='const fs=require("fs");const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports.run;console.log(f(0x0f0f0f0f,0x01010101,0))'
        vals[variant]=int(subprocess.check_output(['node','-e',code,str(dst)],text=True).strip())
    assert vals['strict-unmasked']!=vals['masked']
    q.save(out/'wrong-anchor.json',dict(values=vals,input=[252645135,16843009,0],expected=16843009,reason='table[0] is 1, not zero'))
    # Byte masks other than 1, side effects, and unsupported shapes must fail closed.
    bads={
        'step-two':p.source([('add',1,0)]).replace('i8x16 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1','i8x16 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2'),
        'memory':p.source([('add',1,0)]).replace('(module','(module (memory 1)',1),
        'no-step':p.module(q.masked(p.splat(0))),
    }
    rejected=[]
    for name,text in bads.items():
        f=out/(name+'.wasm');q.compile(text,f)
        try:p.transform(f,out/(name+'-converted.wasm'),'anchor-free')
        except q.Unsupported as e:rejected.append(dict(name=name,status='rejected',reason=str(e)))
        else:raise AssertionError(name+' should reject')
    q.save(out/'rejected.json',rejected)
    print(json.dumps(dict(checked_clones=len(rows),algebra_checks=checks,wrong_anchor=vals,rejected=len(rejected))))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
