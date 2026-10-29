'use strict';
const fs=require('fs');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const f=e[process.argv[3]];
e.init(0x12345678);f(100);
const ns=[];for(let i=0;i<9;i++){
  const start=process.hrtime.bigint();f(500);ns.push(Number(process.hrtime.bigint()-start)/500);
}
console.log(JSON.stringify({ns,checksum:e.checksum(),rss_kib:process.resourceUsage().maxRSS,warmup:100,batch:500,batches:9}));
