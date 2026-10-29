'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
const file=process.argv[2],b=Number(process.argv[3]);
const memory=new WebAssembly.Memory({initial:1,maximum:1,shared:true});new Uint32Array(memory.buffer).fill(b);
const api=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file)),{env:{memory}}).exports;
let sink=0;for(let i=0;i<128;i++){api.store(0,0);sink^=api.bench(128,0);}
function timed(n){api.store(0,0);const t=process.hrtime.bigint();const v=api.bench(n,0);const ns=Number(process.hrtime.bigint()-t);assert.equal(api.load(0)>>>0,n);sink^=v;return ns;}
let n=1024;while(n<2**22&&timed(n)<8e6)n*=2;
const samples=Array.from({length:9},()=>timed(n)/n),sorted=samples.slice().sort((a,b)=>a-b);
console.log(JSON.stringify({file,node:process.version,v8:process.versions.v8,warmupCalls:128,warmupIterations:128,n,samples,median:sorted[4],rssKiB:process.resourceUsage().maxRSS,linearMemoryBytes:memory.buffer.byteLength,sink}));
