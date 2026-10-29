'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const origin=path.resolve(__dirname,'../sha-phase-witness/artifacts');
const bytes=fs.readFileSync(path.join(origin,'before.wasm'));
const manifest=JSON.parse(fs.readFileSync(path.join(origin,'manifest.json')));
assert.equal(sha(bytes),manifest.artifacts['before.wasm'].sha256);
const api=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
const rows=JSON.parse(fs.readFileSync(path.join(__dirname,'artifacts/cases.json')));
for(const row of rows){
 const input=Buffer.from(row.message_hex,'hex'),memory=Buffer.from(api.memory.buffer);
 assert.equal(input.length,64); input.copy(memory,1024);
 assert.equal(api.hash(input.length),512);
 assert.equal(memory.subarray(512,544).toString('hex'),row.digest);
 assert.equal(sha(input),row.digest);
 assert.deepEqual(memory.subarray(1024,1088),input);
}
const result={node:process.version,v8:process.versions.v8,full_wasm_hash_checks:rows.length,
 binary_sha256:sha(bytes),script_sha256:sha(fs.readFileSync(__filename)),
 cases_sha256:sha(fs.readFileSync(path.join(__dirname,'artifacts/cases.json'))),
 limits:'Baseline full-hash validation only; V-window witness is checked in Python, not instrumented Wasm.'};
const target=path.join(__dirname,'artifacts/verification.json');
fs.writeFileSync(target,JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result,null,2));
