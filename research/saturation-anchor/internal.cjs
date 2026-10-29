'use strict';
const fs=require('fs');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const f=e[process.argv[3]];
const warmup=20000,batch=50000;
e.init(0x12345678);f(warmup);
const ns=[];for(let i=0;i<9;i++){
  const start=process.hrtime.bigint();f(batch);ns.push(Number(process.hrtime.bigint()-start)/batch);
}
console.log(JSON.stringify({ns,checksum:e.checksum(),rss_kib:process.resourceUsage().maxRSS,warmup,batch,batches:9}));
