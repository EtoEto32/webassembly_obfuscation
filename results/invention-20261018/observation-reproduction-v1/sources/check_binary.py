"""Initial full binary path test. Performance/adaptive suite remains separate."""
import json
from pathlib import Path
import subprocess
import sys
import transform

out=Path(sys.argv[1]).resolve()
if out.exists():
    raise SystemExit('Refuse overwrite')
out.mkdir(parents=True)
source=['mul',['add',['mul','v0','v1'],['mul','v2','v0']],['add',['mul','v1','v2'],1]]
wat='(module (memory (export "memory") 1 1) (func (export "run") (param i32 i32 i32) (result i32) (i32.store (i32.const 16) (local.get 0)) '+transform.emit(transform.wat(source))+' (i32.load (local.get 0)) i32.add))'
# Folded outer addition includes a load and is intentionally NOT a pure region.
base=out/'plain.wasm';wp=out/'plain.wat';wp.write_text(wat,encoding='utf-8')
transform.tool('wat2wasm',[wp,'-o',base])
reports=[]
for mode in ('output-only','random','frontier'):
    reports.append(transform.transform(base,out/(mode+'.wasm'),mode))
js=r'''
const fs=require('fs'),path=require('path');
(async()=>{
 const dir=process.argv[2],modes=['plain','output-only','random','frontier'];
 const ex=await Promise.all(modes.map(async m=>(await WebAssembly.instantiate(fs.readFileSync(path.join(dir,m+'.wasm')))).instance.exports));
 let seed=20261018;const rand=()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;};
 const inputs=[];for(const x of [0,1,4,16,65532,65533,65536,0xffffffff])for(const y of [0,1,0xffffffff])for(const z of [0,1,0x80000000])inputs.push([x,y,z]);
 for(let i=0;i<1024;i++)inputs.push([i%2?rand():rand()%65536,rand(),rand()]);
 function obs(e,row){new Uint8Array(e.memory.buffer).fill(0);let value=null,trap=null;try{value=e.run(...row);}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=err.message;}return {value,trap,bytes:Buffer.from(new Uint8Array(e.memory.buffer))};}
 const rows=modes.map(mode=>({mode,checks:0,mismatches:0,traps:0}));
 for(const input of inputs){const expected=obs(ex[0],input);for(let i=0;i<ex.length;i++){const got=obs(ex[i],input);rows[i].checks++;if(got.trap)rows[i].traps++;if(got.value!==expected.value||got.trap!==expected.trap||!got.bytes.equals(expected.bytes))rows[i].mismatches++;}}
 fs.writeFileSync(path.join(dir,'inputs.json'),JSON.stringify(inputs));fs.writeFileSync(path.join(dir,'runtime.json'),JSON.stringify({node:process.version,v8:process.versions.v8,rows},null,2));
 console.log(JSON.stringify(rows));if(rows.some(x=>x.mismatches))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
(out/'verify.cjs').write_text(js,encoding='utf-8')
subprocess.run(['node',str(out/'verify.cjs'),str(out)],check=True)
(out/'summary.json').write_text(json.dumps({'source':source,'mode_regions':[len(r['regions']) for r in reports],
    'limitations':['One program, raw only; includes observable store and following OOB load.',
                   'No performance or general obfuscation conclusion.']},indent=2),encoding='utf-8')
