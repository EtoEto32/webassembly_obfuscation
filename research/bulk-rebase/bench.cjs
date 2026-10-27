'use strict';const fs=require('fs');
const [file,ds,ss,ls]=process.argv.slice(2),d=+ds,s=+ss,n=+ls;
const code=fs.readFileSync(file),t=process.hrtime.bigint(),moduleObject=new WebAssembly.Module(code);
const compile_ms=Number(process.hrtime.bigint()-t)/1e6,u=process.hrtime.bigint();
const e=new WebAssembly.Instance(moduleObject).exports,instantiate_ms=Number(process.hrtime.bigint()-u)/1e6;
const warmup=Math.ceil(262144/n),batch=Math.ceil(1048576/n),ns=[];
e.fill(0x12345678);e.bench(warmup,d,s,n);
for(let i=0;i<9;i++){const start=process.hrtime.bigint();e.bench(batch,d,s,n);ns.push(Number(process.hrtime.bigint()-start)/batch);}
let checksum=2166136261;for(let i=0;i<65536;i++)checksum=Math.imul(checksum^e.read(i),16777619)>>>0;
console.log(JSON.stringify({ns,checksum,compile_ms,instantiate_ms,rss_kib:process.resourceUsage().maxRSS,warmup,batch,batches:9}));
