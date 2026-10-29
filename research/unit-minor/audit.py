import argparse
import itertools
import json
import platform
import random
import re
import shutil
import subprocess
from pathlib import Path
import prototype as p
import recover
import run as mainrun


def oracle(name, xyz, mask=p.MASK):
    x,y,z=xyz
    if name=='bilinear': v=(x+y)*(z+7)-x*z
    elif name=='horner': v=((3*x+y)*x+z)*x+17
    else: v=(x+y+3)*(y+z+5)*(z+x+7)
    return v&mask


def exact_det(a):
    # Fraction-free integer elimination; independent of modular odd-pivot kernel.
    a=[r[:] for r in a]; n=len(a); prev=1; sign=1
    for k in range(n-1):
        i=next((i for i in range(k,n) if a[i][k]),None)
        if i is None: return 0
        if i!=k: a[k],a[i]=a[i],a[k]; sign=-sign
        pivot=a[k][k]
        for i in range(k+1,n):
            for j in range(k+1,n):
                num=a[i][j]*pivot-a[i][k]*a[k][j]
                assert num%prev==0
                a[i][j]=num//prev
            a[i][k]=0
        prev=pivot
    return sign*a[-1][-1]


def modular_det(a, width):
    a=[r[:] for r in a]; mask=(1<<width)-1; n=len(a); acc=1
    for k in range(n-1):
        pivot=next(((i,j) for i in range(k,n) for j in range(k,n) if a[i][j]&1),None)
        if pivot is None: raise ArithmeticError('no odd pivot')
        i,j=pivot
        if i!=k: a[i],a[k]=a[k],a[i]; acc=-acc
        if j!=k:
            for row in a: row[j],row[k]=row[k],row[j]
            acc=-acc
        q=a[k][k]; inv=pow(q,-1,1<<width); acc=acc*q&mask
        for i in range(k+1,n):
            factor=a[i][k]*inv&mask
            for j in range(k,n): a[i][j]=(a[i][j]-factor*a[k][j])&mask
    return acc*a[-1][-1]&mask


def run(main, output):
    main,out=Path(main).resolve(),Path(output).resolve(); out.mkdir(parents=True,exist_ok=False)
    accepted=recover.templates(out/'templates'); rows=json.loads((main/'manifest.json').read_text())
    model=[]; rng=random.Random(221042)
    for name in mainrun.FIXTURES:
        src=main/f'{name}.plain.raw.wasm'; t=p.source(src); m=p.matrix(t); c,q,_=p.mix(m,221040)
        for mode,mat in (('unmixed',m),('constant',c),('polynomial',q)):
            # Compare polynomial identity only after recovery, never supply it to the attacker.
            normal,stats=recover.determinant(mat)
            assert normal==p.to_poly(t)
            for width in (2,3,32):
                mask=(1<<width)-1
                inputs=list(itertools.product(range(1<<width),repeat=3)) if width<32 else [tuple(rng.getrandbits(32) for _ in range(3)) for _ in range(256)]
                even=0; zero=0
                for xyz in inputs:
                    a=[[p.eval_poly(v,xyz,mask) for v in line] for line in mat]
                    got=modular_det(a,width); expected=oracle(name,xyz,mask)
                    assert got==expected==(exact_det(a)&mask)
                    even+=not(got&1); zero+=got==0
                model.append(dict(name=name,mode=mode,width=width,cases=len(inputs),even_outputs=even,zero_outputs=zero,mismatch=0))
    p.save(out/'model.json',dict(seed=221042,rows=model,cases=sum(x['cases'] for x in model)))
    regenerated=[]; interpreter=[]
    probes=[(0,0,0),(1,2,3),(0xffffffff,0xffffffff,0xffffffff),(0x80000000,1,7),(0x7fffffff,0x80000000,65535),(2,2,2),(0,7,0),(255,65535,3)]
    for row in rows:
        if row['negative']: continue
        src=main/row['file']; dst=out/row['file']
        if row['mode'].endswith('-recovered'):
            protected=main/row['file'].replace('.recovered.wasm','.wasm')
            recover.recover(protected,dst,accepted)
        elif row['opt']=='O3':
            p.tool('wasm-opt',[out/row['file'].replace('.O3.wasm','.raw.wasm'),'-O3','-o',dst])
        elif row['mode']=='plain':
            expr=mainrun.FIXTURES[row['name']]
            p.compile_wat(f'(module (func (export "run") (param i32 i32 i32) (result i32) {expr}))',dst)
        else: p.transform(main/f'{row["name"]}.plain.raw.wasm',dst,row['mode'])
        assert dst.read_bytes()==src.read_bytes()
        regenerated.append(dict(file=src.name,sha256=p.digest(src),byte_equal=True))
        mod=p.read(src); index=next(x[2][1] for x in mod[1:] if x[0]=='export' and x[1]=='"run"')
        for k,xyz in enumerate(probes):
            args=' '.join('(i32.const '+p.signed(x)+')' for x in xyz)
            mod.append(p.sx.parse(f'(module (func (export "probe{k}") (result i32) (call {index} {args})))')[1])
        wrapper=out/(src.stem+'.probe.wasm'); p.compile_wat(p.sx.emit(mod),wrapper)
        text=p.tool('wasm-interp',[wrapper,'--run-all-exports'])
        found=[int(v)&p.MASK for v in re.findall(r'probe\d+\(\) => i32:(-?\d+)',text)]
        assert found==[oracle(row['name'],xyz) for xyz in probes],text
        interpreter.append(dict(file=src.name,calls=len(probes),outputs=found))
    p.save(out/'replay.json',regenerated); p.save(out/'interpreter.json',interpreter)
    controls=[]
    for row in rows:
        if not row['negative']: continue
        try: recover.extract(main/row['file'],accepted)
        except ValueError as e: controls.append(dict(file=row['file'],status='rejected',reason=str(e)))
        else: raise AssertionError('modified kernel accepted')
    # A valid kernel can trap on a matrix outside the unit-minor condition.
    bad=out/'insufficient-rank.wasm'; p.compile_wat(p.kernel(p.payload([[p.const(2),{}],[{},p.const(2)]])),bad)
    try: recover.extract(bad,accepted)
    except ValueError as e: controls.append(dict(file=bad.name,status='rejected',reason=str(e)))
    else: raise AssertionError('rank deficient matrix accepted')
    js="const fs=require('fs');let e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;let trapped=false;try{e.run(0,0,0)}catch(x){trapped=x instanceof WebAssembly.RuntimeError}console.log(JSON.stringify({trapped}));if(!trapped)process.exit(1)"
    r=subprocess.run(['node','-e',js,str(bad)],capture_output=True,text=True,check=True)
    controls[-1]['runtime']=json.loads(r.stdout)
    for name,extra,expr in [('memory','(memory 1)','(local.get 0)'),('xor','','(i32.xor (local.get 0) (local.get 1))')]:
        f=out/('source-'+name+'.wasm'); p.compile_wat(f'(module {extra} (func (export "run") (param i32 i32 i32) (result i32) {expr}))',f)
        try: p.source(f)
        except ValueError as e: controls.append(dict(file=f.name,status='rejected',reason=str(e)))
        else: raise AssertionError('unsupported source accepted')
    p.save(out/'controls.json',controls)
    p.save(out/'environment.json',dict(platform=platform.platform(),python=platform.python_version(),processor=platform.processor(),node=subprocess.check_output(['node','--version'],text=True).strip(),wabt=p.tool('wasm-validate',['--version']).strip(),binaryen=p.tool('wasm-opt',['--version']).strip()))
    p.save(out/'commands.json',p.LOG); mainrun.pin(out)
    print(json.dumps(dict(model_cases=sum(x['cases'] for x in model),regenerated=len(regenerated),interpreter_calls=sum(x['calls'] for x in interpreter),controls=len(controls))))


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('main'); ap.add_argument('output'); a=ap.parse_args(); run(a.main,a.output)
