import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import assert from 'node:assert/strict';
const dir=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));let calls=0;
for(const row of manifest.normalizations)for(const file of [row.original,row.lowered]){const trace=[],ex=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(dir,file))),{env:{touch:()=>trace.push('touch')}}).exports;
 let outcome='return';try{ex.entry();}catch(err){if(!(err instanceof WebAssembly.RuntimeError))throw err;outcome='trap';}calls++;
 assert.deepEqual({outcome,calls:trace,memory:crypto.createHash('sha256').update(new Uint8Array(ex.memory.buffer)).digest('hex')},row.expected,file);
}
const result={refusals:manifest.refusals.length,normalizations:manifest.normalizations.length,entryCalls:calls,node:process.version};fs.writeFileSync(path.join(dir,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
