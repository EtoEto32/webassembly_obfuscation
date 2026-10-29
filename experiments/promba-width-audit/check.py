"""Finite width-policy audit; does not execute ProMBA or an SMT solver."""
import hashlib
import json
import math
import platform
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parents[1]/'tmp/contextual-mba-followup'


def falling(t,width):
    mask=(1<<width)-1
    product=1
    for j in range(10):
        product=(product*((t-j)&mask))&mask
    return product


def selected_width(c):
    return 8 if c<=16 else 12 if c<=256 else 24 if c<=65536 else 32 if c<=16777216 else 64


def smt(width,constrained=False):
    t='(bvand x (_ bv1 '+str(width)+'))' if constrained else 'x'
    factors=[f'(bvsub {t} (_ bv{j} {width}))' for j in range(10)]
    product=factors[0]
    for factor in factors[1:]:
        product=f'(bvmul {product} {factor})'
    return f'(set-logic QF_BV)\n(declare-const x (_ BitVec {width}))\n(assert (not (= (bvadd {product} {t}) {t})))\n(check-sat)\n'


def main():
    path=ROOT/'results.json'
    if path.exists(): raise FileExistsError(path)
    verification=json.loads((SOURCE/'verification.json').read_text())
    checked=[]
    for row in verification['source_files']:
        if row['file'] not in ('main.ml','utils.ml'): continue
        data=(SOURCE/row['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==row['sha256']
        assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_blob']
        checked.append(row)
    assert len(checked)==2
    assert selected_width(9)==8
    exhaustive=[dict(x=x,left=(falling(x,8)+x)&255,right=x) for x in range(256)]
    assert all(r['left']==r['right'] for r in exhaustive)
    controls=[]
    for width in (8,32,64):
        for bit in (0,1):
            assert falling(bit,width)==0
        value=(falling(10,width)+10)&((1<<width)-1)
        controls.append(dict(width=width,x=10,left=value,right=10,equal=value==10))
    assert controls[0]['equal'] and not controls[1]['equal'] and not controls[2]['equal']
    assert math.factorial(10)==3628800 and math.factorial(10)%256==0
    files=[]
    for width,constrained in [(8,False),(32,False),(64,False),(32,True)]:
        name=f'query-{width}-'+('constrained' if constrained else 'generalized')+'.smt2'
        (ROOT/name).write_text(smt(width,constrained))
        files.append(name)
    result=dict(python=platform.python_version(),commit=verification['commit'],
                source_verified=checked,selected_width=8,exhaustive=exhaustive,controls=controls,
                original_constraint='t=x&1; falling(t)=0 since t is 0 or 1',
                solver_executed=False,author_program_executed=False,
                queries=files,hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['check.py','protocol.json']+files})
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(selected_width=8,exhaustive_checks=256,controls=controls,
                         solver_executed=False,author_program_executed=False),indent=2))


if __name__=='__main__': main()
