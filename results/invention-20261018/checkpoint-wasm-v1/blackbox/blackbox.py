"""Five public samples suffice to clone an integer polynomial of degree <= 4.

The degree/integer-polynomial promise is necessary. Unknown programs are not certified.
"""
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from probe import mul
from wasm_gate import assemble, horner


def learn(outputs,bits=32):
    """Only outputs at consecutive PUBLIC inputs 0..4 are consumed."""
    if len(outputs)!=5:raise ValueError('Need outputs at 0..4')
    m=1<<bits;diff=[x%m for x in outputs];falling=[1];out=[0]*5;ds=[]
    for k in range(5):
        d=diff[0];ds.append(d);fact=math.factorial(k);v=0
        while fact%2==0:fact//=2;v+=1
        if d%(1<<v):raise ValueError('Not an integer-coefficient polynomial of degree <= 4')
        weight=(d>>v)*pow(fact,-1,m)%m
        for i,c in enumerate(falling):out[i]=(out[i]+weight*c)%m
        diff=[(b-a)%m for a,b in zip(diff,diff[1:])]
        falling=mul(falling,[-k%m,1],m)
    return out,ds


def run(root):
    dest=root/'blackbox';dest.mkdir(exist_ok=False)
    m=json.loads((root/'manifest.json').read_text())
    # The runner reads the bytes to instantiate, but the learner sees only these five outputs.
    js='''const fs=require('fs'),path=require('path');const dir=process.argv[1];
const m=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let rows=[];
for(const r of m.rows.filter(x=>x.mode==='composed')){const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,r.wasm)))).exports.run;
 rows.push({wasm:r.wasm,outputs:[0,1,2,3,4].map(x=>f(x)>>>0)});}console.log(JSON.stringify(rows));'''
    answers=json.loads(subprocess.check_output([shutil.which('node'),'-e',js,str(root)],text=True,timeout=30))
    (dest/'queries.json').write_text(json.dumps(answers,indent=2),encoding='utf-8')
    rows=[]
    for a in answers:
        p,d=learn(a['outputs'])
        bp=dest/a['wasm'];assemble(horner(p,['local.get','0']),bp.with_suffix('.wat'),bp)
        # Only after reconstruction consult reference metadata for differential scoring.
        origin=next(r for r in m['rows'] if r['wasm']==a['wasm'])
        rows.append({'wasm':bp.name,'source':origin['source'],'learned_coefficients':p,'differences':d})
    (dest/'manifest.json').write_text(json.dumps({'rows':rows},indent=2),encoding='utf-8')
    # Reuse the independent BigInt scoring harness, not the polynomial learner.
    subprocess.run([shutil.which('node'),'-e',(root/'source/check.cjs').read_text(),str(dest)],check=True,timeout=30)
    # Deliberate out-of-promise control: five values do not certify an arbitrary program.
    p,_=learn([x**5 for x in range(5)])
    def val(p,x):
        r=0
        for c in reversed(p):r=(r*x+c)%(1<<32)
        return r
    assert val(p,5)!=5**5
    (dest/'control.json').write_text(json.dumps({'outside_promise':'x^5',
        'learned_value_at_5':val(p,5),'oracle_value_at_5':5**5,
        'conclusion':'The learner relies on the degree promise; sample agreement alone is not a certificate.'},indent=2),encoding='utf-8')
    shutil.copy2(__file__,dest/'blackbox.py')
    print(json.dumps({'conditions':len(rows),'public_queries_per_condition':5,'degree_promise':4}))


if __name__=='__main__':run(Path(sys.argv[1]))
