'use strict';const fs=require('fs');let t=performance.now();const m=new WebAssembly.Module(fs.readFileSync(process.argv[2])),compile_ms=performance.now()-t;t=performance.now();const f=new WebAssembly.Instance(m).exports.run,instantiate_ms=performance.now()-t;let x=123456789,h=0;
const run=n=>{for(let i=0;i<n;i++){x=(Math.imul(x,1664525)+1013904223)|0;h=(h+f(x,h,x^0x12345678))|0;}};
run(50000);const ns=[];for(let k=0;k<9;k++){t=performance.now();run(20000);ns.push((performance.now()-t)*1e6/20000);}
console.log(JSON.stringify({compile_ms,instantiate_ms,ns,checksum:h,warmup:50000,batch:20000,repeats:9,peak_rss_kib:process.resourceUsage().maxRSS,linear_memory_bytes:0}));
