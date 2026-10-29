'use strict';
const fs=require('fs'),{performance}=require('perf_hooks');
const bench=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports.bench;
let checksum=bench(16384,0x435210),count=256;
function measure(n,s){const start=performance.now();checksum^=bench(n,s);return performance.now()-start;}
for(let i=0;i<12;i++){const ms=measure(count,i+1);if(ms>=20)break;count=Math.min(0x10000000,Math.max(count*2,Math.ceil(count*25/Math.max(ms,.01))));}
const samples=[];for(let i=0;i<7;i++){const ms=measure(count,0x20261022+i);samples.push({milliseconds:ms,ns:ms*1e6/count});}
process.stdout.write(JSON.stringify({file:process.argv[2],count,samples,checksum,maxRSSKiB:process.resourceUsage().maxRSS,node:process.version,v8:process.versions.v8}));
