'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const task=JSON.parse(fs.readFileSync(process.argv[2]));
const api=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(task.file))).exports;
function checksum(n){let s=0;for(let i=0;i<n;i++){s=(((s<<1)|(s>>>31))+(task.answers[i%task.answers.length]>>>0))>>>0;}return s;}
for(let i=0;i<128;i++)assert.equal(api.bench(16)>>>0,checksum(16));
let sink=0;
function timed(n){const t=process.hrtime.bigint();const v=api.bench(n)>>>0;const ns=Number(process.hrtime.bigint()-t);assert.equal(v,checksum(n));sink^=v;return ns;}
let n=1024;while(n<2**18&&timed(n)<5e6)n*=2;
const samples=Array.from({length:9},()=>timed(n)/n),ordered=samples.slice().sort((a,b)=>a-b);
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,warmupCalls:128,warmupIterations:16,n,
 samples,median_ns:ordered[4],maxRSS_KiB:process.resourceUsage().maxRSS,sink,checksum:checksum(n)}));
