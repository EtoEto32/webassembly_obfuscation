const fs=require('fs'),os=require('os'),{performance}=require('perf_hooks');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;e.memory.grow(1);let sum=0;
const pattern=process.argv[3]||'mixed';
function batch(count){for(let i=0;i<count;i++){const flag=pattern==='zero'?0:pattern==='one'?1:Math.imul(i,1103515245)>>>31;
 sum^=e.run((i&31)*64,4096+(i&31)*64,16,(i&15)>>>0,flag);}}
batch(10000);const samples=[];for(let i=0;i<9;i++){const t=performance.now();batch(30000);samples.push((performance.now()-t)*1e6/30000)}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,pattern,samples_ns:samples,warmup:10000,repetitions:9,calls_per_repetition:30000,
 checksum:sum,public_memory_bytes:e.memory.buffer.byteLength,max_rss_kib:process.resourceUsage().maxRSS}));
