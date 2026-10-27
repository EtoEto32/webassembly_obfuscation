import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let apiCalls=0,hostCalls=0;
for(const row of manifest.runtime){const runs=[];for(const file of row.binaries){let ex;const hostTrace=[];const touch=()=>{hostCalls++;hostTrace.push({name:'touch',write:row.write});if(row.write)new Uint8Array(ex.memory.buffer)[7]=0;};
 ex=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,file))),{env:{touch}}).exports;let trap=false;try{ex.entry();}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;trap=true;}apiCalls++;
 const memory=Buffer.from(ex.memory.buffer);runs.push({outcome:{trap},hostTrace,memory:{sha256:crypto.createHash('sha256').update(memory).digest('hex'),bytes7to10:Array.from(memory.subarray(7,11))}});
}assert.deepEqual(runs,row.runs,row.name);}
assert.equal(apiCalls,manifest.apiCalls);assert.equal(hostCalls,manifest.hostCalls);
const result={contracts:manifest.rows.length,apiCalls,hostCalls,unsat:manifest.unsat,unknown:manifest.unknown,node:process.version};fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
