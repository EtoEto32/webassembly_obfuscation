'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const out=path.resolve(process.argv[2]||path.join(__dirname,'artifacts'));
const resultPath=path.join(out,'verification.json');
if(fs.existsSync(resultPath))throw Error('Refuse overwrite verification');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
for(const [name,record] of Object.entries(manifest.artifacts))assert.equal(sha(fs.readFileSync(path.join(out,name))),record.sha256,name);
const cases=JSON.parse(fs.readFileSync(path.join(out,'cases.json'))),observations=[];
for(const name of ['before.wasm','capture.raw.wasm','capture.O2.wasm']){
 const api=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(out,name)))).exports;
 const memory=Buffer.from(api.memory.buffer),capture=name!=='before.wasm';
 const rows=[];let rejected=0;
 for(const [id,row] of cases.entries()){
  const message=Buffer.from(row.message,'hex');assert.equal(message.length,32);assert.equal(sha(message),row.digest);
  memory.fill(0xa5,640,672);message.copy(memory,1024);
  assert.equal(api.hash(message.length),512);
  const digest=memory.subarray(512,544).toString('hex');assert.equal(digest,row.digest);
  const state=Array.from({length:8},(_,i)=>memory.readUInt32LE(640+4*i));
  if(capture)assert.deepEqual(state,row.target,`${name} ${id}`);
  else assert.ok(memory.subarray(640,672).every(x=>x===0xa5));
  assert.deepEqual(memory.subarray(1024,1056),message);
  rows.push({id,digest,state:capture?state:null});
  if(capture){
   const wrong=Buffer.from(message);wrong.swap32();wrong.copy(memory,1024);api.hash(32);
   const wrongState=Array.from({length:8},(_,i)=>memory.readUInt32LE(640+4*i));
   if(wrongState.some((x,i)=>x!==row.target[i]))rejected++;
   if(id===0)rows[0].negative_control={message:wrong.toString('hex'),state:wrongState};
  }
 }
 if(capture)assert.ok(rejected>0);
 observations.push({name,cases:rows.length,state_checks:capture?rows.length:0,negative_mismatches:rejected,rows});
}
fs.writeFileSync(resultPath,JSON.stringify({node:process.version,v8:process.versions.v8,openssl:process.versions.openssl,script_sha256:sha(fs.readFileSync(__filename)),manifest_sha256:sha(fs.readFileSync(path.join(out,'manifest.json'))),observations},null,2)+'\n');
console.log(JSON.stringify(observations.map(({rows,...summary})=>summary),null,2));
