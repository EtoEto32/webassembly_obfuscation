"""Check why higher polynomial degree alone does not remove the quotient."""
import argparse
import json
from pathlib import Path
import random
import prototype as p
from run import save,command
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False);rng=random.Random(20261019);checks=0;zero_cases=0
    def one(width,b,y,coeff):
        nonlocal checks,zero_cases
        modulus=1<<width;mask=modulus-1
        def f(z):return (coeff[0]+coeff[1]*z+coeff[2]*z*z+coeff[3]*z*z*z)&mask
        w=b*y&mask
        if b==0:assert b*f(y)&mask==0;zero_cases+=1;return
        g=b&-b;small=modulus//g;h=b//g;representative=((w//g)*pow(h,-1,small))%small if small>1 else 0
        other=(y+small)&mask
        assert (b*f(y)&mask)==(b*f(representative)&mask)==(b*f(other)&mask)
        checks+=1
    for width in range(1,9):
        for b in range(1<<width):
            for y in range(1<<width):one(width,b,y,[1,3,5,7])
    for _ in range(10000):one(32,rng.getrandbits(32),rng.getrandbits(32),[rng.getrandbits(32) for _ in range(4)])
    target=a.output/'rotation.wasm';p.compile_wat('(module (func (export "run") (param i32 i32 i32) (result i32) (i32.mul (local.get 1) (i32.rotr (local.get 0) (local.get 2)))))',target)
    witnesses=command(['node','-e',"const fs=require('fs');const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;let rows=[];for(let r=1;r<=31;r++){let b=2**r,delta=2**(32-r),k=32-r;let before=[Math.imul(b,0),Math.imul(b,delta)],after=[e.run(0,b,k),e.run(delta,b,k)];if(before[0]!==before[1]||after[0]===after[1])throw Error('missing counterexample');rows.push({r,b,delta,k,before,after});}console.log(JSON.stringify(rows));",target])
    result=dict(polynomial_nonzero_b_checks=checks,zero_b_checks=zero_cases,polynomial_mismatches=0,rotation_counterexamples=len(witnesses),rotation_calls=2*len(witnesses),witnesses=witnesses,seed=20261019)
    save(a.output/'results.json',result);print(json.dumps({k:v for k,v in result.items() if k!='witnesses'}))
if __name__=='__main__':main()
