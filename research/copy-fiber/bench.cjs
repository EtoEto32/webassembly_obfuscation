'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict'),{performance}=require('node:perf_hooks');
const args=process.argv.slice(2),b=fs.readFileSync(args[0]);assert(WebAssembly.validate(b));
const ex=new WebAssembly.Instance(new WebAssembly.Module(b)).exports;
const correctness_checksum=ex.bench(257)>>>0;
for(let i=0;i<32;i++)ex.bench(32);
let n=32,calibration_ms=0,checksum=0;
while(true){const start=performance.now();checksum^=ex.bench(n);calibration_ms=performance.now()-start;if(calibration_ms>=10||n>=65536)break;n*=2;}
const ns=[];for(let j=0;j<7;j++){const start=performance.now();checksum^=ex.bench(n);ns.push((performance.now()-start)*1e6/n);}
const sort=ns.slice().sort((a,b)=>a-b),r={node:process.version,v8:process.versions.v8,flags:process.execArgv,warmup:{calls:32,iterations_per_call:32},iterations:n,calibration_ms,batches_ns:ns,median_ns:sort[3],checksum:checksum>>>0,correctness_checksum,rss_bytes:process.memoryUsage().rss,max_rss_kib:process.resourceUsage().maxRSS};
fs.writeFileSync(args[1],JSON.stringify(r,null,2));console.log(JSON.stringify(r));
