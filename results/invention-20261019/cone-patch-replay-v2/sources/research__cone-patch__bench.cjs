'use strict';const fs=require('fs'),f=process.argv[2],name=process.argv[3];let t=performance.now();const m=new WebAssembly.Module(fs.readFileSync(f));const compile_ms=performance.now()-t;t=performance.now();const e=new WebAssembly.Instance(m).exports;const instantiate_ms=performance.now()-t;let x=123456789,h=0;
const run=n=>{for(let i=0;i<n;i++){x=(Math.imul(x,1664525)+1013904223)|0;h=(h+e[name](x&3,x,h^0x12345678))|0;}};
run(100000);const ns=[];for(let k=0;k<9;k++){t=performance.now();run(50000);ns.push((performance.now()-t)*1e6/50000);}
console.log(JSON.stringify({compile_ms,instantiate_ms,ns,checksum:h,warmup:100000,batch:50000,repeats:9,peak_rss_kib:process.resourceUsage().maxRSS,linear_memory_bytes:65536}));
