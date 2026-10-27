const fs=require('fs'),os=require('os'),{performance}=require('perf_hooks');const fn=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports.run;
const inputs=Array.from({length:1024},(_,i)=>Array.from({length:8},(_,j)=>Math.imul(i+17*j,2654435761)));let checksum=0;
function batch(n){for(let i=0;i<n;i++){const a=inputs[i&1023];checksum^=fn(a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7]);}}
batch(20000);const times=[];for(let i=0;i<9;i++){const t=performance.now();batch(20000);times.push((performance.now()-t)*1e6/20000);}
console.log(JSON.stringify({samples_ns:times,checksum,max_rss_kib:process.resourceUsage().maxRSS,warmup:20000,repetitions:9,calls_per_repetition:20000,node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model}));
