'use strict';const fs=require('fs'),assert=require('assert');
const load=f=>new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(f))).exports;
const e=load(process.argv[2]),d=process.argv[4]==='zero'?1:0,seed=0x12345678;
e.bench(1024,seed,d);let batch=32;const calibration=[];
for(;;){const t=process.hrtime.bigint();e.bench(batch,seed,d);const elapsed=Number(process.hrtime.bigint()-t);calibration.push({batch,elapsed_ns:elapsed});if(elapsed>=1e7||batch>=2**20)break;batch*=2;}
const ns=[],checks=[];
for(let k=0;k<9;k++){const t=process.hrtime.bigint(),c=e.bench(batch,seed,d);ns.push(Number(process.hrtime.bigint()-t)/batch);checks.push(c);}
const rss_kib=process.resourceUsage().maxRSS,b=load(process.argv[3]),want=b.bench(batch,seed,d);
for(const c of checks)assert.strictEqual(c,want);
console.log(JSON.stringify({ns,batch,calibration,checksum:want,rss_kib}));
