const fs=require('fs');const run=new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(process.argv[2]))).exports.run;
let sink=0;for(let i=0;i<10000;i++)sink^=run(i*71717,i*13331);
const samples=[];for(let r=0;r<11;r++){const begin=process.hrtime.bigint();for(let i=0;i<10000;i++)sink^=run(i*71717,i*13331);samples.push(Number(process.hrtime.bigint()-begin)/10000);}
samples.sort((a,b)=>a-b);console.log(JSON.stringify({median_ns:samples[5],samples_ns:samples,maxRSS_KiB:process.resourceUsage().maxRSS,warmup:10000,calls_per_sample:10000,repetitions:11,sink}));
