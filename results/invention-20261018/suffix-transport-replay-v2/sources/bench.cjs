const fs=require('fs'),os=require('os'),{performance}=require('perf_hooks');
const exp=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports;
const mem=new Uint8Array(exp.memory.buffer);
let seed=20261018;for(let i=0;i<mem.length;i++){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;mem[i]=seed&255;}
let checksum=0;
const rows=[];
for(const length of [32,512]){
  function batch(n){for(let i=0;i<n;i++)checksum^=exp.run((i&31)*1024,length);}
  batch(200);
  const samples=[];
  for(let k=0;k<9;k++){const start=performance.now();batch(200);samples.push((performance.now()-start)*1e6/200);}
  rows.push({length,warmup_calls:200,repetitions:9,calls_per_repetition:200,samples_ns_per_call:samples});
}
console.log(JSON.stringify({rows,checksum,linear_memory_bytes:mem.length,max_rss_kib:process.resourceUsage().maxRSS,
  node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,platform:process.platform,arch:process.arch}));
