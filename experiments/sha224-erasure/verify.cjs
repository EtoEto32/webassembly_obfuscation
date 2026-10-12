'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=__dirname,out=path.resolve(process.argv[2]||path.join(root,'artifacts'));
const baseline=path.resolve(root,'../sha256-research-baseline/artifacts');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const hash=b=>crypto.createHash('sha224').update(b).digest('hex');
if(fs.existsSync(path.join(out,'verification.json')))throw Error('Refuse overwrite verification');
const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json')));
const inputIndex=JSON.parse(fs.readFileSync(path.join(baseline,'inputs.json'))),bundle=fs.readFileSync(path.join(baseline,'inputs.bin'));
assert.equal(sha(bundle),inputIndex.bundle_sha256);
const cases=inputIndex.cases.map(t=>({...t,input:bundle.subarray(t.offset,t.offset+t.length)}));
for(const t of cases)t.expected=hash(t.input); // SHA-256 expected values are never reused.
assert.equal(cases.find(t=>t.id==='empty').expected,'d14a028c2a3a2bc9476102bb288234c415a2b01f828ea62ac5b3e42f');
assert.equal(cases.find(t=>t.id==='abc').expected,'23097d223405d8228642a477bda255b32aadbce4bda0b3f7e36c9da7');
for(const n of [1,55,56,63,64,65,1048576])assert.ok(cases.some(t=>t.length===n));
const results=[],eighthWords={};
for(const row of manifest.files){
 const binary=fs.readFileSync(path.join(out,row.file));assert.equal(sha(binary),row.sha256);
 const api=new WebAssembly.Instance(new WebAssembly.Module(binary)).exports,mem=new Uint8Array(api.memory.buffer);
 const observations=[];eighthWords[row.mode]=[];
 for(const t of cases){
  mem.set(t.input,1024);mem.fill(0xa5,1024+t.length,1024+t.length+64);mem.fill(0xcc,540,544);
  const ptr=api.hash(t.length);assert.equal(ptr,512);
  const digest=Buffer.from(mem.slice(ptr,ptr+28)).toString('hex');
  assert.deepEqual(mem.subarray(1024,1024+t.length),new Uint8Array(t.input),'input changed');
  assert.ok(mem.subarray(1024+t.length,1024+t.length+64).every(v=>v===0xa5));
  assert.ok(mem.subarray(540,544).every(v=>v===0xcc),'wrote a 256-bit digest');
  if(row.mode==='plain'||row.mode==='erasure')assert.equal(digest,t.expected,row.mode+' '+t.id);
  eighthWords[row.mode].push(new DataView(mem.buffer).getUint32(412,true));
  observations.push({id:t.id,length:t.length,digest,match:digest===t.expected});
 }
 const rejected=[];
 for(const n of [1048577,0x7fffffff,0x80000000,0xffffffff]){
  const before=sha(mem);assert.throws(()=>api.hash(n),WebAssembly.RuntimeError);assert.equal(sha(mem),before);rejected.push(n);
 }
 // A valid call after rejected lengths checks reinitialization and reuse.
 mem.set(Buffer.from('abc'),1024);api.hash(3);
 if(row.mode==='plain'||row.mode==='erasure')assert.equal(Buffer.from(mem.slice(512,540)).toString('hex'),hash(Buffer.from('abc')));
 const failures=observations.filter(t=>!t.match);
 if(row.mode==='bad-no-compensation')assert.ok(failures.some(t=>t.id==='abc'));
 if(row.mode==='bad-every-block'){
  assert.ok(observations.find(t=>t.id==='abc').match,'one padded block should not distinguish this control');
  for(const n of [56,63,64,65])assert.ok(failures.some(t=>t.id==='length-'+n),'last-block guard control '+n);
 }
 results.push({mode:row.mode,cases:cases.length,mismatches:failures.length,rejected_lengths:rejected,observations});
}
const witnesses=cases.flatMap((t,i)=>eighthWords.plain[i]!==eighthWords.erasure[i]?[{id:t.id,plain:eighthWords.plain[i],erasure:eighthWords.erasure[i]}]:[]);
assert.ok(witnesses.length>0,'internal state must actually change');
const report={node:process.version,v8:process.versions.v8,openssl:process.versions.openssl,reference:'Node crypto SHA-224 (OpenSSL); independent of Wasm generator',script_sha256:sha(fs.readFileSync(__filename)),bundle_sha256:sha(bundle),positive_comparisons:cases.length*2,internal_state_changed_cases:witnesses.length,first_internal_witness:witnesses[0],results};
fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({...report,results:results.map(({observations,...r})=>r)},null,2));
