'use strict';
const fs=require('fs');const t0=performance.now(),m=new WebAssembly.Module(fs.readFileSync(process.argv[2])),compile_ms=performance.now()-t0,t1=performance.now(),f=new WebAssembly.Instance(m).exports.bench,instantiate_ms=performance.now()-t1;
let x=0x123456789abcdefn;x=f(100000,x);const ns=[];for(let j=0;j<9;j++){const t=performance.now();x=f(20000,x);ns.push((performance.now()-t)*1e6/20000);}
console.log(JSON.stringify({compile_ms,instantiate_ms,ns,checksum:String(x),warmup:100000,batch:20000,repeats:9,peak_rss_kib:process.resourceUsage().maxRSS,heap_used_bytes:process.memoryUsage().heapUsed,node:process.version,v8:process.versions.v8}));
