import json
import re
import subprocess
import sys
from pathlib import Path
import prototype as p

main,out=map(lambda x:Path(x).resolve(),sys.argv[1:]);out.mkdir(parents=True,exist_ok=False)
rows=json.loads((main/'manifest.json').read_text());replay=[];interpreter=[]
for row in rows:
    dst=out/row['file'];text=p.history(row['rotation'],row['mask']) if row['mode']=='history' else p.source(row['rotation'],row['mask'])
    if row['opt']=='O3' and row['mode']!='recovered':
        raw=out/(dst.stem+'-preopt.wasm');p.q.compile(text,raw);p.q.tool('wasm-opt',[raw,'-O3','-o',dst])
    else:p.q.compile(text,dst)
    assert dst.read_bytes()==(main/row['file']).read_bytes();replay.append(dst.name)
    m=p.q.read(dst);index=next(x[2][1] for x in m[1:] if x[:2]==['export','"run"'])
    count=len([x for x in m[1:] if x[0]=='func'])
    cases=[(0,0),(1,1),(0x80000000,1),(0xffffffff,2),(0x12345678,31),(0x12345678,32),(0x12345678,33),(0xffffffff,64)]
    for j,(seed,n) in enumerate(cases):
        m.extend([['func',['result','i32'],['call',index,['i32.const',str(seed)],['i32.const','0'],['i32.const',str(n)]]],
                  ['export','"probe'+str(j)+'"',['func',str(count+j)]]])
    probe=out/('interp-'+dst.name);p.q.compile(p.q.w.emit(m),probe)
    stdout=p.q.w.tool('wasm-interp',[probe,'--run-all-exports']);(out/(probe.stem+'.log')).write_text(stdout,encoding='utf-8')
    got={int(a):int(b) for a,b in re.findall(r'probe(\d+)\(\) => i32:(\d+)',stdout)}
    expected=[p.rot(seed,n*row['rotation'])&row['mask'] for seed,n in cases]
    assert [got[j] for j in range(len(cases))]==expected
    interpreter.append(dict(file=dst.name,expected=expected,actual=got))
p.q.save(out/'replay.json',replay);p.q.save(out/'interpreter.json',dict(calls=8*len(rows),rows=interpreter))
# At least 32-m residual bits are required after identical finite suffixes.
dynamic=[]
js='''const fs=require('fs'),assert=require('assert'),e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[1]))).exports;
const m=+process.argv[2],v=new DataView(e.memory.buffer);let pairs=[];const h=17;
for(let bit=m;bit<32;bit++){let before=[],after=[];
for(const prefix of [0,2**bit]){new Uint8Array(e.memory.buffer).fill(0);v.setUint32(0,prefix,true);v.setUint32(4*(h+1),32-bit,true);
before.push(Array.from({length:h+2},(_,n)=>e.run(0,0,n)>>>0));after.push(e.run(0,0,h+2)>>>0);}
assert.deepStrictEqual(before[0],before[1]);assert.deepStrictEqual(after,[0,1]);pairs.push({bit,previous_outputs_equal:true,next_outputs:after});}
console.log(JSON.stringify({low_bits:m,h,pairs}));'''
for m in (5,16,24,31):
    raw=out/f'dynamic-m{m}-raw.wasm';p.q.compile(p.source(0,(1<<m)-1,True),raw)
    for opt in ('raw','O3'):
        f=raw if opt=='raw' else out/f'dynamic-m{m}-O3.wasm'
        if opt=='O3':p.q.tool('wasm-opt',[raw,'-O3','-o',f])
        proc=subprocess.run(['node','-e',js,str(f),str(m)],capture_output=True,text=True,timeout=30)
        proc.check_returncode();dynamic.append(dict(file=f.name,**json.loads(proc.stdout)))
p.q.save(out/'dynamic-bit-probes.json',dynamic)
p.q.save(out/'environment.json',dict(node=subprocess.check_output(['node','--version'],text=True).strip(),
    python=sys.version,wabt=p.q.w.tool('wasm-validate',['--version']).strip(),binaryen=p.q.tool('wasm-opt',['--version']).strip()))
print(json.dumps(dict(byte_replays=len(replay),interpreter_calls=8*len(rows),dynamic_bit_pairs=sum(len(x['pairs']) for x in dynamic))))
