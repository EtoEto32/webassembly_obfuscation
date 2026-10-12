'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.join(__dirname,'artifacts'),out=path.join(root,'erasure');
const report=JSON.parse(fs.readFileSync(path.join(out,'results.json'))),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
let s=0x19d07c35;function rng(){s^=s<<13;s^=s>>>17;s^=s<<5;return s>>>0;}
const inputs=[],edges=[0,1,2,3,0x7fffffff,0x80000000,0xfffffffe,0xffffffff];
for(const x of edges)for(const y of edges)for(const n of [0,1,2,31,63,64,65,0xffffffff])inputs.push([x,y,n]);
for(let i=0;i<4096;i++)inputs.push([rng(),rng(),rng()]);
assert.equal(sha(JSON.stringify(inputs)),JSON.parse(fs.readFileSync(path.join(root,'correctness.json'))).input_sha256);
const results=[];
for(const r of report.results){
  const a=fs.readFileSync(path.join(root,r.input)),b=fs.readFileSync(path.join(out,r.output));assert.equal(sha(a),r.input_sha256);assert.equal(sha(b),r.output_sha256);
  const before=new WebAssembly.Instance(new WebAssembly.Module(a),{}).exports,after=new WebAssembly.Instance(new WebAssembly.Module(b),{}).exports;
  let mismatches=0,first;for(const args of inputs){const x=before.run(...args),y=after.run(...args);if(x!==y){mismatches++;first??={args,before:x.toString(),after:y.toString()};}}
  const batchMatch=before.batch(1024,123456)===after.batch(1024,123456);
  results.push({input:r.input,output:r.output,cases:inputs.length,mismatches,first,batchMatch});
}
fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({script_sha256:sha(fs.readFileSync(__filename)),node:process.version,v8:process.versions.v8,input_sha256:sha(JSON.stringify(inputs)),
  oracle:'Original Wasm modules previously checked against separate BigInt reference on these identical inputs.',results},null,2)+'\n');
assert(results.every(r=>!r.mismatches&&r.batchMatch));console.log(JSON.stringify({modules:results.length,comparisons:inputs.length*results.length,mismatches:0}));
