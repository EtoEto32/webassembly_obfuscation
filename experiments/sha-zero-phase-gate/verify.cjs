'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),out=path.resolve(process.argv[2]||path.join(__dirname,'artifacts'));
const target=path.join(out,'verification.json');
if(fs.existsSync(target))throw Error('Refuse overwrite');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
for(const [p,h] of Object.entries(manifest))assert.equal(sha(fs.readFileSync(path.join(root,p))),h);
const prior=path.join(__dirname,'../sha-phase-witness/artifacts');
const original=JSON.parse(fs.readFileSync(path.join(prior,'manifest.json')));
for(const n of ['before.wasm','capture.raw.wasm','capture.O2.wasm'])assert.equal(sha(fs.readFileSync(path.join(prior,n))),original.artifacts[n].sha256);
const r=(x,n)=>((x>>>n)|(x<<(32-n)))>>>0;
function inverse(s,k){
 const [A,B,C,D,E,F,G,H]=s;
 const q=((r(B,2)^r(B,13)^r(B,22))+((B&C)|(D&(B|C))))>>>0;
 const t=(A-q)>>>0;
 return [B,C,D,(E-t)>>>0,F,G,H,(t-(r(F,6)^r(F,11)^r(F,25))-(H^(F&(G^H)))-k)>>>0];
}
function encode(s,b){let z=s.slice();for(let i=b-1;i>=8;i--)z=inverse(z,[0xd807aa98,0x12835b01][i-8]);return z;}
const cases=JSON.parse(fs.readFileSync(path.join(out,'cases.json'))),results=[];
for(const name of ['before.wasm','capture.raw.wasm','capture.O2.wasm']){
 const api=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path.join(prior,name)))).exports;
 const memory=Buffer.from(api.memory.buffer),rows=[];
 for(const c of cases){
  const msg=Buffer.from(c.message,'hex');assert.equal(msg.length,64);assert.equal(sha(msg),c.digest);
  memory.fill(0xa5,640,736);msg.copy(memory,1024);assert.equal(api.hash(64),512);
  assert.equal(memory.subarray(512,544).toString('hex'),c.digest);assert.deepEqual(memory.subarray(1024,1088),msg);
  const trace={};let z=null,znext=null;
  if(name==='before.wasm')assert.ok(memory.subarray(640,736).every(x=>x===0xa5));
  else{
   for(const b of [8,9,10]){trace[b]=Array.from({length:8},(_,i)=>memory.readUInt32LE(640+32*(b-8)+4*i));assert.deepEqual(trace[b],c.trace[b]);}
   z=encode(trace[c.phase],c.phase);znext=encode(trace[c.phase+1],c.phase+1);
   assert.deepEqual(z,c.z);assert.deepEqual(znext,c.znext);
  }
  rows.push({phase:c.phase,digest:c.digest,trace,z,znext});
 }
 if(name!=='before.wasm'){assert.deepEqual(rows[0].z,rows[1].z);assert.notDeepEqual(rows[0].znext,rows[1].znext);}
 results.push({name,rows});
}
const report={node:process.version,v8:process.versions.v8,full_digest_checks:6,boundary_state_checks:12,encoded_counterexample_conditions:2,results};
fs.writeFileSync(target,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({full_digest_checks:6,boundary_state_checks:12,encoded_counterexample_conditions:2}));
