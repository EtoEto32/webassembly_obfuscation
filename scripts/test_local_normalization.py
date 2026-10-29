"""Execute only locally generated tiny integer tests, never mining binaries."""
import hashlib
import json
import random
import subprocess
from pathlib import Path
from normalize_wat_local import normalize,signed

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/countermeasures/local-normalization/synthetic-tests'
WAT2WASM=ROOT/'.tools/wabt-1.0.42/bin/wat2wasm.exe'
NODE=Path('C:/Program Files/nodejs/node.exe')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rng=random.Random(20261010)
    functions=[];expected={}
    for bits in [32,64]:
        edge=[0,1,-1,(1<<(bits-1))-1,-(1<<(bits-1)),(1<<bits)-1]
        operands=[(x,y) for x in edge for y in edge]+[(rng.randrange(-(1<<(bits-1)),1<<bits),rng.randrange(-(1<<(bits-1)),1<<bits)) for _ in range(40)]
        for kind in ['add','sub','mul','and','or','xor']:
            for x,y in operands:
                name=f'case{len(functions)}'
                value={'add':lambda:x+y,'sub':lambda:x-y,'mul':lambda:x*y,'and':lambda:x&y,'or':lambda:x|y,'xor':lambda:x^y}[kind]()
                expected[name]=str(signed(value,bits))
                functions.append(f'  (func ${name} (export "{name}") (result i{bits})\n    i{bits}.const {x}\n    nop\n    i{bits}.const {y}\n    i{bits}.{kind}\n  )\n')
    wat='(module\n'+''.join(functions)+')\n';normalized,events=normalize(wat)
    assert normalize(normalized)[0]==normalized,'Not idempotent'
    controls={
        'float': '    f64.const 1\n    f64.const 2\n    f64.add\n',
        'division': '    i32.const 1\n    i32.const 0\n    i32.div_s\n',
        'call_barrier': '    i32.const 1\n    call $side_effect\n    i32.const 2\n    i32.add\n',
        'control_barrier': '    i32.const 1\n    block\n    i32.const 2\n    end\n    i32.add\n',
        'memory': '    i32.const 1\n    i32.load\n    i32.const 2\n    i32.add\n'}
    for name,code in controls.items():
        candidate='(module\n  (func $control\n'+code+'  )\n)\n'
        assert normalize(candidate)[0]==candidate,name
    data='(module\n  (data (i32.const 0) "nop i32.const 1 i32.const 2 i32.add")\n)\n'
    assert normalize(data)[0]==data
    for name,text in [('original',wat),('normalized',normalized)]:
        p=OUT/(name+'.wat');p.write_text(text,encoding='utf-8')
        subprocess.run([str(WAT2WASM),str(p),'-o',str(p.with_suffix('.wasm'))],check=True,timeout=30)
    (OUT/'expected.json').write_text(json.dumps(expected),encoding='utf-8')
    runner=OUT/'check.cjs'
    runner.write_text("'use strict';\nconst fs=require('fs'),path=require('path');\nconst expected=JSON.parse(fs.readFileSync(path.join(__dirname,'expected.json')));\nlet checked=0;for(const name of ['original','normalized']){const bytes=fs.readFileSync(path.join(__dirname,name+'.wasm'));const instance=new WebAssembly.Instance(new WebAssembly.Module(bytes),{});for(const [fn,value] of Object.entries(expected)){if(String(instance.exports[fn]())!==value)throw Error(name+': '+fn);checked++;}}\nconsole.log(JSON.stringify({checked,modules:2,network_used:false,mining_code:false}));\n",encoding='utf-8')
    r=subprocess.run([str(NODE),str(runner)],capture_output=True,text=True,timeout=30,check=True)
    report=dict(status='passed',runtime=json.loads(r.stdout),functions=len(expected),events=len(events),untouched_negative_patterns=list(controls)+['data string'],
                normalizer_sha256=hashlib.sha256((ROOT/'scripts/normalize_wat_local.py').read_bytes()).hexdigest(),
                scope='Synthetic integer edge/random tests only; not public hashing vectors, real-world prevalence or all-input equivalence.')
    (OUT/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
