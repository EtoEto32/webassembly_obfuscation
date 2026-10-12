'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const out=path.resolve(process.argv[2]||path.join(__dirname,'artifacts'));
const target=path.join(out,'verification.json');
if(fs.existsSync(target))throw Error('Refuse overwrite');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
for(const [n,r] of Object.entries(manifest.artifacts))assert.equal(sha(fs.readFileSync(path.join(out,n))),r.sha256);
const cases=JSON.parse(fs.readFileSync(path.join(out,'cases.json'))),results=[];
for(const name of ['before.wasm','capture.raw.wasm','capture.O2.wasm']){
 const api=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(out,name)))).exports;
 const memory=Buffer.from(api.memory.buffer),instrumented=name!=='before.wasm',rows=[];
 for(const row of cases){
  const message=Buffer.from(row.message,'hex');assert.equal(message.length,64);assert.equal(sha(message),row.digest);
  memory.fill(0xa5,640,736);message.copy(memory,1024);assert.equal(api.hash(64),512);
  const digest=memory.subarray(512,544).toString('hex');assert.equal(digest,row.digest);
  assert.deepEqual(memory.subarray(1024,1088),message);
  const trace={};
  if(instrumented)for(const b of [8,9,10]){
   trace[b]=Array.from({length:8},(_,i)=>memory.readUInt32LE(640+32*(b-8)+4*i));
   assert.deepEqual(trace[b],row.trace[b]);
  }else assert.ok(memory.subarray(640,736).every(x=>x===0xa5));
  rows.push({id:row.id,digest,trace});
 }
 if(instrumented){
  assert.deepEqual(rows[0].trace[8],rows[1].trace[9]);
  assert.notDeepEqual(rows[0].trace[9],rows[1].trace[10]);
  assert.equal(cases[0].W,cases[1].W);
 }
 assert.notEqual(rows[0].digest,rows[1].digest);
 results.push({name,rows});
}
fs.writeFileSync(target,JSON.stringify({node:process.version,v8:process.versions.v8,script_sha256:sha(fs.readFileSync(__filename)),manifest_sha256:sha(fs.readFileSync(path.join(out,'manifest.json'))),results},null,2)+'\n');
console.log(JSON.stringify({full_digest_checks:6,boundary_state_checks:12,equal_state_different_successor_witnesses:2},null,2));
