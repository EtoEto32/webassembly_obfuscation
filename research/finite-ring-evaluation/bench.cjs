'use strict';const fs=require('fs'),assert=require('assert');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const seed=0x2468ace1;e.bench(128,seed);let batch=32,calibration=[];
for(;;){const t=process.hrtime.bigint();e.bench(batch,seed);const elapsed=Number(process.hrtime.bigint()-t);calibration.push({batch,elapsed_ns:elapsed});if(elapsed>=1e7||batch>=2**22)break;batch*=2;}
const ns=[],checks=[];for(let i=0;i<9;i++){const t=process.hrtime.bigint(),c=e.bench(batch,seed);ns.push(Number(process.hrtime.bigint()-t)/batch);checks.push(c);}
const rotr=(a,n)=>(a>>>n)|(a<<(32-n));let want=0;
for(let i=0;i<batch;i++){const a=(seed+i)|0,b=seed^i,c=(i<<11)|(i>>>21);want^=((rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c)))|0;}
for(const c of checks)assert.strictEqual(c,want);
console.log(JSON.stringify({ns,checksum:want,batch,calibration,rss_kib:process.resourceUsage().maxRSS,warmup:128,batches:9}));
