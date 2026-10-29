const fs=require('fs'),os=require('os'),{performance}=require('perf_hooks');
const e=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const n=e.run.length,args=Array.from({length:n},(_,i)=>Math.imul(i+7,0x1234567)),memory=new Uint8Array(e.memory.buffer);
function batch(count){for(let i=0;i<count;i++){args[0]=(i&31)*128;args[1]=(args[1]+17)|0;e.run(...args)}}
batch(10000);const samples=[];for(let r=0;r<11;r++){const t=performance.now();batch(50000);samples.push((performance.now()-t)*1e6/50000);}
console.log(JSON.stringify({node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,samples_ns:samples,warmup:10000,repetitions:11,calls_per_repetition:50000,
 checksum:memory.reduce((a,b)=>a+b,0),public_memory_bytes:memory.length,max_rss_kib:process.resourceUsage().maxRSS}));
