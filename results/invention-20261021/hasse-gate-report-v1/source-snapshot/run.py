"""Generate, recover and check the predeclared four coefficient experiments."""
import argparse
import json
import platform
import random
import shutil
import subprocess
import sys
from pathlib import Path
import prototype as p


def fixtures():
    for name,order in [('cubic',1),('sextic',2),('dodecic',4),('degree31',16)]:
        d=p.DAG(); x=d.node('x',0); y=d.node('x',1)
        def a(u,v): return d.op('add',u,v)
        def s(u,v): return d.op('sub',u,v)
        def m(u,v): return d.op('mul',u,v)
        def c(n): return d.const(n)
        def power(v,n):
            if n==0: return c(1)
            if n==1: return v
            t=power(v,n//2); z=m(t,t)
            return m(z,v) if n%2 else z
        if name=='cubic': r=m(m(a(x,y),s(x,y)),a(m(c(3),x),m(c(5),y)))
        if name=='sextic': r=power(a(a(m(x,x),m(x,y)),m(y,y)),3)
        if name=='dodecic': r=power(a(power(x,3),power(y,3)),4)
        if name=='degree31':
            r=m(m(power(a(x,m(c(3),y)),16),power(s(x,m(c(5),y)),8)),
                m(m(power(a(m(c(7),x),y),4),power(a(x,y),2)),s(m(c(11),x),m(c(3),y))))
        yield name,order,d,r


def run(out):
    out=Path(out).resolve(); out.mkdir(parents=True,exist_ok=False)
    manifest={'cases':[], 'targets':[], 'controls':[], 'environment':{'python':sys.version,'platform':platform.platform()}}
    srcs=out/'sources'; srcs.mkdir()
    dependencies=[*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*.cjs'),
                  p.ROOT/'research/isotope-swizzle/prototype.py',p.ROOT/'research/connectivity-elimination/prototype.py']
    for src in dependencies:
        dest=srcs/('__'.join(src.relative_to(p.ROOT).parts)); shutil.copy2(src,dest)
    for name,k,d,root in fixtures():
        original=out/(name+'.source.raw.wasm'); p.q.compile(p.emit(d,root),original)
        transformed=out/(name+'.jet.raw.wasm'); meta=p.transform(original,transformed,k)
        manifest['cases'].append(dict(name=name,order=k,nodes=d.nodes,root=root,transform=meta))
        for mode,raw in [('source',original),('jet',transformed)]:
            optimized=out/(name+'.'+mode+'.O3.wasm'); p.q.tool('wasm-opt',[raw,'-O3','-o',optimized]); p.q.w.tool('wasm-validate',[optimized])
            for opt,path in [('raw',raw),('O3',optimized)]:
                recovered=out/(path.stem+'.recovered.wasm')
                try: rec=p.recover(path,recovered); status='recovered'
                except p.Unsupported as exc: rec={'reason':str(exc)}; status='unsupported'
                manifest['targets'].append(dict(name=name,mode=mode,opt=opt,file=path.name,bytes=path.stat().st_size,
                    sha256=p.q.digest(path),recovered=recovered.name if status=='recovered' else None,status=status,recovery=rec))
    controls={
      'even-factor':('(i32.mul (local.get 0) (local.get 0))',1),
      'inhomogeneous':('(i32.add (i32.mul (local.get 0) (local.get 0)) (local.get 0))',1),
      'xor':('(i32.xor (local.get 0) (local.get 1))',1),
      'order-too-large':('(local.get 0)',2)}
    for name,(expr,k) in controls.items():
        f=out/('reject-'+name+'.wasm'); p.q.compile('(module (func (export "run") (param i32 i32) (result i32) '+expr+'))',f)
        try: p.transform(f,out/(f.stem+'.bad.wasm'),k)
        except p.Unsupported as exc: manifest['controls'].append(dict(name=name,status='rejected',reason=str(exc)))
        else: raise AssertionError('accepted negative '+name)
    # These two polynomials represent the zero function modulo 2^32; their formal derivatives differ.
    for name,expr in {
        'zero':'(i32.const 0)',
        'null-polynomial':'(i32.mul (i32.const 2147483648) (i32.mul (local.get 0) (i32.sub (local.get 0) (i32.const 1))))',
        'null-derivative':'(i32.mul (i32.const 2147483648) (i32.sub (i32.mul (i32.const 2) (local.get 0)) (i32.const 1)))'
    }.items(): p.q.compile('(module (func (export "run") (param i32 i32) (result i32) '+expr+'))',out/('control-'+name+'.wasm'))
    p.q.save(out/'manifest.json',manifest)
    result=subprocess.run(['node',str(Path(__file__).with_name('check.cjs')),str(out)],capture_output=True,text=True,timeout=90)
    (out/'check.stdout.txt').write_text(result.stdout,encoding='utf-8'); (out/'check.stderr.txt').write_text(result.stderr,encoding='utf-8')
    if result.returncode: raise RuntimeError(result.stderr)
    source_coeff={}
    for row in manifest['targets']:
        if row['status']!='recovered': continue
        coeff=row['recovery']['coefficients']
        if row['name'] in source_coeff: assert coeff==source_coeff[row['name']]
        source_coeff[row['name']]=coeff
    pins={str(f.relative_to(out)):p.q.digest(f) for f in out.rglob('*') if f.is_file()}
    p.q.save(out/'pins.json',pins)
    print(json.dumps({'directory':str(out),'targets':len(manifest['targets']),'recovered':sum(t['status']=='recovered' for t in manifest['targets'])}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args();run(a.output)
