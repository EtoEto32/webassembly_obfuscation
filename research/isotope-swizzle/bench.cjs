'use strict';const fs=require('fs');const bytes=fs.readFileSync(process.argv[2]);
let t=performance.now();const mod=new WebAssembly.Module(bytes);const compile_ms=performance.now()-t;t=performance.now();const e=new WebAssembly.Instance(mod).exports;const instantiate_ms=performance.now()-t;
let x=123456789,check=0;const batch=n=>{for(let i=0;i<n;i++){x=(Math.imul(x,1664525)+1013904223)|0;check=(check+e.run(x,x^0x36572418,x+check))|0;}};
batch(50000);const ns=[];for(let k=0;k<9;k++){t=performance.now();batch(50000);ns.push((performance.now()-t)*1e6/50000);}
console.log(JSON.stringify({compile_ms,instantiate_ms,ns,checksum:check,peak_rss_kib:process.resourceUsage().maxRSS,linear_memory_bytes:0,warmup:50000,batch:50000,repeats:9}));
