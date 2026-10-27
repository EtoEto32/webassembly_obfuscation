'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
async function main(){
 const [dir,file,method,lengthText]=process.argv.slice(2),length=Number(lengthText);
 const {instance}=await WebAssembly.instantiate(fs.readFileSync(path.join(dir,file)));
 new Uint8Array(instance.exports.memory.buffer).fill(0);
 const len=length+16,run=instance.exports.run;
 assert.equal(run(0,len),-1);
 const warmup=method==='plain'?10000:8;
 const iterations=method==='plain'?200000:(method==='rolling'?8:2);
 let checksum=0;
 for(let i=0;i<warmup;i++)checksum^=run(0,len);
 const ns=[];
 for(let r=0;r<7;r++){
   const t=process.hrtime.bigint();for(let i=0;i<iterations;i++)checksum^=run(0,len);
   ns.push(Number(process.hrtime.bigint()-t)/iterations);
 }
 console.log(JSON.stringify({file,method,length,haystack_bytes:len,case:'all-zero no match',warmup,iterations,
  ns_per_call:ns,median_ns:[...ns].sort((a,b)=>a-b)[3],peak_rss_KiB:process.resourceUsage().maxRSS,
  exposed_memory_bytes:instance.exports.memory.buffer.byteLength,checksum,node:process.version,v8:process.versions.v8}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
