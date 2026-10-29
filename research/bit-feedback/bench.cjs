const fs=require('fs'),os=require('os'),{performance}=require('perf_hooks');
const bytes=fs.readFileSync(process.argv[2]);const fn=new WebAssembly.Instance(new WebAssembly.Module(bytes)).exports.run;
let checksum=0;const input=Array.from({length:1024},(_,i)=>[Math.imul(i,2654435761),Math.imul(i+3,2246822519)]);
for(let i=0;i<10000;i++){const p=input[i&1023];checksum^=fn(p[0],p[1]);}
const samples=[];for(let r=0;r<9;r++){const start=performance.now();for(let i=0;i<10000;i++){const p=input[i&1023];checksum^=fn(p[0],p[1]);}samples.push((performance.now()-start)*1e6/10000);}
console.log(JSON.stringify({samples_ns:samples,checksum,max_rss_kib:process.resourceUsage().maxRSS,memory:process.memoryUsage(),node:process.version,v8:process.versions.v8,cpu:os.cpus()[0].model,warmup:10000,repetitions:9,calls_per_repetition:10000}));
