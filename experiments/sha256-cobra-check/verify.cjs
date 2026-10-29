'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const base=path.join(__dirname,'../sha256-research-baseline/artifacts'),out=path.join(__dirname,'artifacts/rewritten');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
if(fs.existsSync(path.join(out,'verification.json')))throw Error('Refuse overwrite');
const index=JSON.parse(fs.readFileSync(path.join(base,'inputs.json'))),input=fs.readFileSync(path.join(base,'inputs.bin'));
assert.equal(sha(input),index.bundle_sha256);
const manifest=JSON.parse(fs.readFileSync(path.join(out,'manifest.json'))),results=[];
for(const row of manifest.files){
 const binary=fs.readFileSync(path.join(out,row.binary));assert.equal(sha(binary),row.output_sha256);
 const api=new WebAssembly.Instance(new WebAssembly.Module(binary)).exports,mem=new Uint8Array(api.memory.buffer),outputs=[];
 for(const t of index.cases){
  const bytes=input.subarray(t.offset,t.offset+t.length);assert.equal(sha(bytes),t.expected);
  mem.set(bytes,1024);mem.fill(0xa5,1024+t.length,1024+t.length+64);
  assert.equal(api.hash(t.length),512);
  const actual=Buffer.from(mem.slice(512,544)).toString('hex');assert.equal(actual,t.expected);
  assert.equal(sha(mem.subarray(1024,1024+t.length)),t.expected);
  assert.ok(mem.subarray(1024+t.length,1024+t.length+64).every(x=>x===0xa5));outputs.push({id:t.id,actual});
 }
 for(const length of [1048577,0x7fffffff,0x80000000,0xffffffff]){
  const before=sha(mem);assert.throws(()=>api.hash(length),WebAssembly.RuntimeError);assert.equal(sha(mem),before);
 }
 mem.set(Buffer.from('abc'),1024);assert.equal(api.hash(3),512);assert.equal(Buffer.from(mem.slice(512,544)).toString('hex'),index.cases[1].expected);
 results.push({binary:row.binary,checks:outputs.length,mismatches:0,outputs});
}
fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({node:process.version,v8:process.versions.v8,script_sha256:sha(fs.readFileSync(__filename)),input_sha256:sha(input),results},null,2));
console.log(JSON.stringify(results.map(({outputs,...r})=>r),null,2));
