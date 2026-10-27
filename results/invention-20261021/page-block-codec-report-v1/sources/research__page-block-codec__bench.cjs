'use strict';
const fs=require('node:fs'),{performance}=require('node:perf_hooks');
const file=process.argv[2],off=Number(process.argv[3]);
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(file))).exports;
const expected=e.bench(257,off);
for(let i=0;i<128;i++)e.bench(64,off);
let n=256,elapsed=0;
do{const t=performance.now();e.bench(n,off);elapsed=performance.now()-t;if(elapsed>=8||n>=4194304)break;n*=2;}while(true);
const raw=[];let checksum=0;
for(let i=0;i<7;i++){const t=performance.now();checksum^=e.bench(n,off);raw.push((performance.now()-t)*1e6/n);}
const sorted=[...raw].sort((a,b)=>a-b);
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,flags:process.execArgv,off,warmup:{calls:128,iterations:64},n,target_ms:8,calibration_ms:elapsed,batches:7,ns:raw,median_ns:sorted[3],expected,checksum,maxRSS_KiB:process.resourceUsage().maxRSS}));
