'use strict';const fs=require('fs');const f=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports.bench;
let a=123456789,b=87654321,c=3456789;function run(n){c=f(n,a,b,c);a=(a+c)|0;b=(b^c)|0;}
run(100000);const ns=[];for(let k=0;k<9;k++){const t=performance.now();run(200000);ns.push((performance.now()-t)*1e6/200000);}
console.log(JSON.stringify({ns,checksum:c,rss_kib:process.resourceUsage().maxRSS,warmup:100000,batch:200000,batches:9}));
