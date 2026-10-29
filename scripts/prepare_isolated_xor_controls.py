"""Isolate two reviewed byte-XOR helpers for non-mining finite tests.

This is a manual selection/host adaptation for checking reviewed state models,
not automatic deobfuscation, whole-miner execution, or a hashing experiment.
"""
import hashlib
import json
import random
import re
from pathlib import Path
from evaluate_local_normalization import ROOT,WABT,run,sha

OUT=ROOT/'results/countermeasures/flattening-xor'
SOURCE=ROOT/'results/runtime-mining/cross-dataset/proof-of-theft'
ALLOWED={'global.get','local.get','local.set','local.tee','i32.const','i32.add','i32.sub','i32.and','i32.xor','i32.eq','i32.eqz','i32.lt_u',
         'i32.load','i32.load8_u','i32.store','i32.store8','block','loop','end','br','br_if','select','return','unreachable'}


def main():
    OUT.mkdir(parents=True,exist_ok=True);functions=[];sources=[];cases=[];rng=random.Random(20261010)
    for length,index in [(8,112),(16,118)]:
        for variant,role in [('original','ref'),('flattening','flat')]:
            path=SOURCE/f'xmr-{variant}-f{index}-reviewed.wat.txt';text=path.read_text(encoding='utf-8')
            lines=text.splitlines()
            assert re.match(r'^  \(func \$f\d+ \(type \$t7\) \(param \$p0 i32\) \(param \$p1 i32\)',lines[0])
            opcodes=[line.strip().split()[0].rstrip(')') for line in lines[2:] if line.strip()]
            assert all(op in ALLOWED for op in opcodes),set(opcodes)-ALLOWED
            assert 'call' not in text and 'global.set' not in text and 'memory.grow' not in text
            name=f'xor{length}_{role}'
            body=re.sub(r'^  \(func \$f\d+ \(type \$t7\)',f'  (func ${name}',text,count=1)
            functions.append(body);functions.append(f'  (export "{name}" (func ${name}))\n')
            sources.append(dict(length=length,role=role,path=str(path.relative_to(ROOT)),sha256=sha(path),opcodes=sorted(set(opcodes))))
        specifications=[('edge',1024,2048,v) for v in [0,1,127,255]]
        specifications += [('uniform',1024,2048,v) for v in range(256)]
        specifications += [('random',1024,2048,None) for _ in range(64)]
        specifications += [('alias',1024,1024+delta,None) for delta in range(-length+1,length)]
        specifications += [('memory-end',65536-length,2048,None),('memory-end',1024,65536-length,None)]
        for label,a,b,value in specifications:
            addresses=sorted(set(range(a,a+length))|set(range(b,b+length)))
            initial=[[address,rng.randrange(256) if value is None else (value if address<a+length and address>=a else 255-value)] for address in addresses]
            cases.append(dict(length=length,label=label,destination=a,source=b,initial=initial))
    module='(module\n  (memory (export "memory") 1 1)\n  (global $g0 (export "stack") (mut i32) (i32.const 32768))\n'+''.join(functions)+')\n'
    wat=OUT/'isolated-xor.wat';wat.write_text(module,encoding='utf-8');binary=wat.with_suffix('.wasm')
    run([WABT/'wat2wasm.exe',wat,'-o',binary]);run([WABT/'wasm-validate.exe',binary])
    (OUT/'cases.json').write_text(json.dumps(cases),encoding='utf-8')
    manifest=dict(sources=sources,wasm_sha256=sha(binary),wat_sha256=sha(wat),cases_sha256=sha(OUT/'cases.json'),
                  cases=len(cases),memory_pages=1,maximum_memory_pages=1,imports=[],hashing=False,
                  adaptation='Selected reviewed helpers retain instruction bodies; remove source type reference and rename functions; supply fixed bounded memory and stack global.',
                  scope='Finite small XOR helper tests; never load full miner. Caller context, whole-module semantics and hash path are not validated.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(dict(cases=len(cases),binary_bytes=binary.stat().st_size,hashing=False)))


if __name__=='__main__':
    main()
