const fs=require('fs'),os=require('os'),{performance}=require('perf_hooks');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const mem=new Uint8Array(e.memory.buffer);let seed=20261018;
for(let i=0;i<mem.length;i++){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;mem[i]=seed&255;}
let checksum=0;const calls=1000;function batch(n){for(let i=0;i<n;i++)checksum^=e.run((i&15)*64,64);}
batch(3000);const samples=[];for(let j=0;j<11;j++){let t=performance.now();batch(calls);samples.push((performance.now()-t)*1e6/calls);}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,checksum,samples_ns:samples,
 warmup:3000,repetitions:11,calls_per_repetition:calls,bytes_per_call:64,public_memory_bytes:e.memory.buffer.byteLength,max_rss_kib:process.resourceUsage().maxRSS}));
