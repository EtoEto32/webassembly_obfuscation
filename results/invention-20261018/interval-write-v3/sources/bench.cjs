const fs=require('fs'),os=require('os'),{performance}=require('perf_hooks');
const bytes=fs.readFileSync(process.argv[2]),n=+process.argv[3];
const e=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports;
let seed=20261018;const inputs=Array.from({length:1024},()=>Array.from({length:n},()=>{seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return seed>>>0;}));
let checksum=0;function batch(count){for(let i=0;i<count;i++)checksum^=e.run(...inputs[i&1023]);}
batch(2000);const samples=[];for(let j=0;j<9;j++){const t=performance.now();batch(10000);samples.push((performance.now()-t)*1e6/10000);}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,checksum,
 samples_ns:samples,warmup:2000,repetitions:9,calls_per_repetition:10000,
 public_memory_bytes:e.memory.buffer.byteLength,max_rss_kib:process.resourceUsage().maxRSS}));
