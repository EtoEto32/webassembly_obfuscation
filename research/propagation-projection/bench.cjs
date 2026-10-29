'use strict';
const fs=require('fs'),assert=require('assert');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const words=new Uint32Array(e.memory.buffer);let state=211032;
for(let i=0;i<words.length;i++){state=(Math.imul(state,1664525)+1013904223)>>>0;words[i]=state;}
const checksum=e.bench(257)>>>0;e.bench(1024);
const measure=count=>{const t=process.hrtime.bigint();const sum=e.bench(count)>>>0;return {elapsed_ns:Number(process.hrtime.bigint()-t),checksum:sum};};
let count=64,pilot;
while(true){pilot=measure(count);if(pilot.elapsed_ns>=1e7||count>=1048576)break;count*=2;}
const samples=Array.from({length:9},()=>measure(count));assert(samples.every(x=>x.checksum===samples[0].checksum));
console.log(JSON.stringify({count,warmup:1024,pilot,samples,ns:samples.map(x=>x.elapsed_ns/count),checksum257:checksum,maxRSSKiB:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8}));
